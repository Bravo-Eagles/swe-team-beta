import requests

class AIRequest:
    """
    Object for managing/sending requests to an AI
    
    Args:
        key: API Key
        url (string, optional): Base api url
        debug (bool, optional): Enables debug messaging
        error (bool, optional): Disables error catching
    """
    def __init__(self, key, url="https://rocky.cs.kent.edu/v1", debug=False, error=True):
        self.url = url 
        self.key = key
        self.debug: bool = debug
        self.error: bool = error
        self.history = []

        # Configs / Defaults
        self.model = 0
        self.streaming = False
        self.store = False
        self.timeout = 390 # Seconds
        self.max_output = 300

        self.headers = {
            "Authorization": f"Bearer {self.key}"
        }

        self.getModels()
        self.setModel()

    def getModels(self):
        """
        Gets & returns list of models

        Returns:
            dict: List of models
        """
        self.models_response = requests.get(
            f"{self.url}/models",
            headers=self.headers,
            timeout=30,
        )
        self.models_response.raise_for_status()
        return self.models_response

    def setModel(self, modelId=None):
        """
        Sets model and retrieves capabilties

        Args:
            modelId (optional): Model ID as listed by getModels()
        """
        if modelId is not None:
            self.model = modelId

        self.model_data = self.models_response.json()["data"][self.model]
        self.capabilities = dict(
            name = self.model_data["id"],
            image_support = self.model_data["metadata"]["supports_image_input"],
            instruction_support = self.model_data["metadata"]["supports_instructions"],
            previous_response_support = self.model_data["metadata"]["supports_previous_response_id"],
            streaming_support = self.model_data["metadata"]["supports_streaming"]
        )

    def send(self, input, instructions=None):
        """
        Sends request to AI
        
        Args:
            input (string): Text the AI receives
            instructions (string, optional): Instructions for the AI 

        Returns:
            dict: API response
        """
        self.payload = {
            "model": self.capabilities['name'],
            "max_output_tokens": self.max_output,
            "store": self.store
        }

        # Adding options to request based on capabilities and user settings
        if instructions is not None:
            if self.capabilities['instruction_support']:
                self.payload |= {"input": input}
                self.payload |= {"instructions": instructions}
            else:
                self.payload |= {"input": f"{instructions}\\n{input}"}
        else:
            self.payload |= {"input": input}
        if self.capabilities['streaming_support'] and self.streaming:
            self.payload |= {"stream": self.streaming}
        
        if self.debug: print(f'Payload: {self.payload}')
        response = requests.post(f'{self.url}/responses', headers=self.headers, json=self.payload, timeout=self.timeout)
        response.raise_for_status()

        return response

