import torch

from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    GenerationConfig
)


MODEL_NAME = "Qwen/Qwen3-4B-Instruct-2507"


class QwenModel:
    def __init__(
        self,
        model_name: str = MODEL_NAME,
        max_new_tokens: int = 512,
        temperature: float = 0.2,
        top_p: float = 0.9
    ):
        self.model_name = model_name

        self.device = (
            "cuda"
            if torch.cuda.is_available()
            else "cpu"
        )

        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name
        )

        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype="auto",
            device_map="auto"
        )

        self.model.eval()

        self.generation_config = GenerationConfig(
            max_new_tokens=max_new_tokens,
            do_sample=temperature > 0,
            temperature=temperature,
            top_p=top_p,
            repetition_penalty=1.05
        )

    def generate(
        self,
        messages: list[dict]
    ) -> str:
        """
        Generate response from chat messages

        messages example:

        [
            {
                "role": "system",
                "content": "You are a database assistant."
            },
            {
                "role": "user",
                "content": "Show all customers from Germany."
            }
        ]
        """

        inputs = self.tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt"
        )

        inputs = {
            key: value.to(self.model.device)
            for key, value in inputs.items()
        }

        with torch.inference_mode():
            outputs = self.model.generate(
                **inputs,
                generation_config=self.generation_config
            )

        generated_tokens = outputs[
            :,
            inputs["input_ids"].shape[1]:
        ]

        response = self.tokenizer.batch_decode(
            generated_tokens,
            skip_special_tokens=True
        )[0]

        return response.strip()


qwen_model = QwenModel()