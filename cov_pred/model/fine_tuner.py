import json
import os
import torch
from transformers import (
    AutoTokenizer, 
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from datasets import Dataset, load_dataset
from peft import LoraConfig, get_peft_model, TaskType
from typing import Dict, List, Optional, Any
import logging


class LocalFineTuner:
    """Hugging Faceを使ったローカルLLMファインチューニング用のクラス"""
    
    def __init__(self, model_name: str = "microsoft/DialoGPT-medium", device: str = None):
        """
        初期化
        
        Args:
            model_name: Hugging Faceモデル名
            device: 使用するデバイス（cuda/cpu）
        """
        self.model_name = model_name
        self.device = device if device else ("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = None
        self.model = None
        self.peft_config = None
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def load_model_and_tokenizer(self, use_lora: bool = True):
        """
        モデルとトークナイザーをロード
        
        Args:
            use_lora: LoRA（Low-Rank Adaptation）を使用するかどうか
        """
        self.logger.info(f"Loading model and tokenizer: {self.model_name}")
        
        # トークナイザーをロード
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # モデルをロード
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            device_map="auto" if self.device == "cuda" else None
        )
        
        if use_lora:
            self._setup_lora()
        
        self.logger.info(f"Model loaded on device: {self.device}")
    
    def _setup_lora(self):
        """LoRA設定をセットアップ"""
        self.peft_config = LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            inference_mode=False,
            r=8,
            lora_alpha=16,
            lora_dropout=0.1,
            target_modules=["q_proj", "v_proj", "k_proj", "o_proj"]
        )
        self.model = get_peft_model(self.model, self.peft_config)
        self.logger.info("LoRA configuration applied")
    
    def prepare_dataset(self, data_path: str, text_column: str = "text") -> Dataset:
        """
        データセットを準備
        
        Args:
            data_path: データファイルのパス（.jsonl または .json）
            text_column: テキストデータのカラム名
            
        Returns:
            準備されたデータセット
        """
        self.logger.info(f"Loading dataset from: {data_path}")
        
        if data_path.endswith('.jsonl'):
            dataset = load_dataset('json', data_files=data_path)['train']
        elif data_path.endswith('.json'):
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            dataset = Dataset.from_list(data)
        else:
            raise ValueError("Unsupported file format. Use .json or .jsonl")
        
        # テキストをトークン化
        def tokenize_function(examples):
            return self.tokenizer(
                examples[text_column],
                truncation=True,
                padding=True,
                max_length=512,
                return_tensors="pt"
            )
        
        tokenized_dataset = dataset.map(tokenize_function, batched=True)
        self.logger.info(f"Dataset prepared with {len(tokenized_dataset)} examples")
        
        return tokenized_dataset
    
    def prepare_conversation_dataset(self, data_path: str) -> Dataset:
        """
        会話データセット用の準備（入力・出力ペア）
        
        Args:
            data_path: 会話データファイルのパス
            
        Returns:
            準備されたデータセット
        """
        self.logger.info(f"Loading conversation dataset from: {data_path}")
        
        with open(data_path, 'r', encoding='utf-8') as f:
            if data_path.endswith('.jsonl'):
                data = [json.loads(line) for line in f]
            else:
                data = json.load(f)
        
        formatted_data = []
        for item in data:
            if 'messages' in item:
                # OpenAI形式
                conversation = ""
                for message in item['messages']:
                    role = message['role']
                    content = message['content']
                    conversation += f"{role}: {content}\n"
                formatted_data.append({"text": conversation.strip()})
            elif 'input' in item and 'output' in item:
                # 入力・出力ペア形式
                text = f"Input: {item['input']}\nOutput: {item['output']}"
                formatted_data.append({"text": text})
        
        dataset = Dataset.from_list(formatted_data)
        
        def tokenize_function(examples):
            return self.tokenizer(
                examples["text"],
                truncation=True,
                padding=True,
                max_length=512,
                return_tensors="pt"
            )
        
        tokenized_dataset = dataset.map(tokenize_function, batched=True)
        self.logger.info(f"Conversation dataset prepared with {len(tokenized_dataset)} examples")
        
        return tokenized_dataset
    
    def train(
        self,
        train_dataset: Dataset,
        val_dataset: Optional[Dataset] = None,
        output_dir: str = "./fine_tuned_model",
        num_train_epochs: int = 3,
        per_device_train_batch_size: int = 4,
        per_device_eval_batch_size: int = 4,
        learning_rate: float = 2e-4,
        warmup_steps: int = 100,
        logging_steps: int = 10,
        save_steps: int = 500,
        eval_steps: int = 500,
        **kwargs
    ) -> str:
        """
        ファインチューニングを実行
        
        Args:
            train_dataset: 訓練データセット
            val_dataset: 検証データセット（オプション）
            output_dir: モデル保存ディレクトリ
            num_train_epochs: エポック数
            per_device_train_batch_size: 訓練時のバッチサイズ
            per_device_eval_batch_size: 評価時のバッチサイズ
            learning_rate: 学習率
            warmup_steps: ウォームアップステップ数
            logging_steps: ログ出力間隔
            save_steps: モデル保存間隔
            eval_steps: 評価実行間隔
            **kwargs: その他のTrainingArguments
            
        Returns:
            保存されたモデルのパス
        """
        self.logger.info("Starting fine-tuning...")
        
        training_args = TrainingArguments(
            output_dir=output_dir,
            overwrite_output_dir=True,
            num_train_epochs=num_train_epochs,
            per_device_train_batch_size=per_device_train_batch_size,
            per_device_eval_batch_size=per_device_eval_batch_size,
            learning_rate=learning_rate,
            warmup_steps=warmup_steps,
            logging_steps=logging_steps,
            save_steps=save_steps,
            eval_steps=eval_steps if val_dataset else None,
            evaluation_strategy="steps" if val_dataset else "no",
            save_strategy="steps",
            load_best_model_at_end=True if val_dataset else False,
            metric_for_best_model="eval_loss" if val_dataset else None,
            fp16=True if self.device == "cuda" else False,
            gradient_checkpointing=True,
            dataloader_pin_memory=False,
            **kwargs
        )
        
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False,
        )
        
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=val_dataset,
            data_collator=data_collator,
            tokenizer=self.tokenizer,
        )
        
        trainer.train()
        
        # モデルを保存
        trainer.save_model()
        self.tokenizer.save_pretrained(output_dir)
        
        self.logger.info(f"Fine-tuning completed. Model saved to: {output_dir}")
        return output_dir
    
    def generate_text(
        self, 
        prompt: str, 
        max_length: int = 100,
        temperature: float = 0.7,
        do_sample: bool = True
    ) -> str:
        """
        テキスト生成
        
        Args:
            prompt: 入力プロンプト
            max_length: 最大生成長
            temperature: 生成の多様性
            do_sample: サンプリングを使用するかどうか
            
        Returns:
            生成されたテキスト
        """
        inputs = self.tokenizer.encode(prompt, return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                inputs,
                max_length=max_length,
                temperature=temperature,
                do_sample=do_sample,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return generated_text[len(prompt):].strip()
    
    def save_model(self, save_path: str):
        """モデルを保存"""
        self.model.save_pretrained(save_path)
        self.tokenizer.save_pretrained(save_path)
        self.logger.info(f"Model saved to: {save_path}")
    
    def load_finetuned_model(self, model_path: str):
        """ファインチューニング済みモデルをロード"""
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            device_map="auto" if self.device == "cuda" else None
        )
        self.logger.info(f"Fine-tuned model loaded from: {model_path}")


def main():
    """使用例"""
    # ファインチューナーを初期化
    fine_tuner = LocalFineTuner(model_name="microsoft/DialoGPT-small")
    
    # モデルとトークナイザーをロード
    fine_tuner.load_model_and_tokenizer(use_lora=True)
    
    # データセットを準備（例：会話データ）
    # train_dataset = fine_tuner.prepare_conversation_dataset("output/zookeeper_1/training.jsonl")
    # val_dataset = fine_tuner.prepare_conversation_dataset("output/zookeeper_1/validation.jsonl")
    
    # ファインチューニングを実行
    # model_path = fine_tuner.train(
    #     train_dataset=train_dataset,
    #     val_dataset=val_dataset,
    #     output_dir="./fine_tuned_zookeeper_model",
    #     num_train_epochs=3,
    #     per_device_train_batch_size=2,
    #     learning_rate=2e-4
    # )
    
    # テキスト生成のテスト
    # prompt = "Input: What is the purpose of ZooKeeper?"
    # generated = fine_tuner.generate_text(prompt, max_length=150)
    # print(f"Generated: {generated}")


if __name__ == "__main__":
    main()