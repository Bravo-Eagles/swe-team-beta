import requests

class AIRequest:
    """
    Object for managing/sending requests to an AI
    
    Args:
        key: API Key
        url (string, optional): Base api url
        debug (bool, optional): Enables debug messaging
        error (bool, optional): Disables error catching
        api_type (string, optional): (Ollama, OpenAI)
    """
    def __init__(self, key, url="https://rocky.cs.kent.edu/v1", debug=False, error=True, api_type="OpenAI"):
        if debug: print('[AIRequest] Initializing\n[AIRequest] Beginning configuration')
        # Input checks
        if not (api_type == "OpenAI" or api_type == "Ollama"):
            raise Exception(f"Invalid api_type: {api_type}")

        # Loading inputs
        self.url = url 
        self.key = key
        self.debug: bool = debug
        self.error: bool = error
        self.history = []
        self.api_type = api_type

        # Check if the given url matches api_type
        if self.error: self.__checkApiType()

        # Configs / Defaults
        self.model = 0
        self.streaming = False
        self.store = False
        self.timeout = 390 # Seconds
        self.max_output = 300

        self.headers = {
            "Authorization": f"Bearer {self.key}"
        }
    
        if self.debug: print('[AIRequest] Configuration complete')

        self.getModels()
        self.setModel()

        if self.debug: print('[AIRequest] Initialization complete')

    def __checkApiType(self):
        self.url.removesuffix("/")
        if self.api_type == "OpenAI":
            if self.url.endswith("api"):
                raise Exception("API url does not match api_type.\napi_type: OpenAI\nURL: Ollama")
            elif not self.url.endswith("v1"):
                if self.url.endswith("/"):
                    self.url += "v1"
                else:
                    self.url += "/v1"
        elif self.api_type == "Ollama":
            if self.url.endswith("v1"):
                raise Exception("API url does not match api_type.\napi_type: Ollama\nURL: OpenAI")
            elif not self.url.endswith("api"):
                if self.url.endswith("/"):
                    self.url += "api"
                else:
                    self.url += "/api"
            

    def getModels(self):
        """
        Gets & returns list of models

        Returns:
            dict: List of models
        """
        if self.debug: print('[AIRequest] getModels')
        payload = ""
        if self.api_type == "OpenAI":
            payload = f"{self.url}/models"
        elif self.api_type == "Ollama":
            payload = f"{self.url}/tags"

        self.models_response = requests.get(
            payload,
            headers=self.headers,
            timeout=30,
        )
        self.models_response.raise_for_status()
        
        if self.debug: print('[AIRequest] getModels complete')
        return self.models_response

    def setModel(self, modelId=None):
        """
        Sets model and retrieves capabilties

        Args:
            modelId (optional): Model ID as listed by getModels()
        """
        if self.debug: print('[AIRequest] setModel')
        if modelId is not None:
            self.model = modelId
            if self.debug: print(f'[AIRequest] Selected model: {self.model}')
        
        if self.api_type == "OpenAI": 
            self.model_data = self.models_response.json()["data"][self.model]
            if "metadata" in self.model_data:
                self.capabilities = dict(
                    name = self.model_data["id"],
                    image_support = self.model_data["metadata"]["supports_image_input"],
                    instruction_support = self.model_data["metadata"]["supports_instructions"],
                    previous_response_support = self.model_data["metadata"]["supports_previous_response_id"],
                    streaming_support = self.model_data["metadata"]["supports_streaming"]
                )
        elif self.api_type == "Ollama":
            self.model_data = self.models_response.json()["models"][self.model]
            model_capabilities = requests.post(
                f"{self.url}/show",
                headers=self.headers,
                json={"model": self.model_data["name"]},
                timeout=30,
            )   
            model_capabilities.raise_for_status()
            self.capabilities = dict(
                name = self.model_data["name"],
                image_support = ("vision" in model_capabilities.json()["capabilities"]),
                instruction_support = True,
                previous_response_support = False,
                streaming_support = True
            )

        if self.debug: print('[AIRequest] setModel complete')

    def send(self, input, instructions=None):
        """
        Sends request to AI
        
        Args:
            input (string): Text the AI receives
            instructions (string, optional): Instructions for the AI 

        Returns:
            dict: API response
        """
        if self.debug: print('[AIRequest] send')
        # Base payload. Only stuff thats universal
        self.payload = {
            "model": self.capabilities['name'],
        }

        # Adding options to payload based on capabilities and user settings
        # Adding generic payload options
        if instructions is not None:
            if self.capabilities['instruction_support']:
                if self.api_type == "OpenAI":
                    self.payload |= {"input": input}
                    self.payload |= {"instructions": instructions}
                elif self.api_type == "Ollama":
                    self.payload |= {"messages": [{"role": "system", "content": instructions}, {"role": "user", "content": input}]}
            else:
                self.payload |= {"input": f"Instructions: {instructions}\n Prompt: {input}"}
        else:
            self.payload |= {"input": input}
        if self.capabilities['streaming_support']:
            self.payload |= {"stream": self.streaming}
        
        if self.debug: print(f'Payload: {self.payload}')
        # Loading api_type specifics for payload
        api_url = ""
        if self.api_type == "OpenAI":
            api_url = f'{self.url}/responses'
            self.payload |= {"max_output_tokens": self.max_output}
            self.payload |= {"store": self.store}
        elif self.api_type == "Ollama": 
            api_url = f'{self.url}/chat'

        response = requests.post(api_url, headers=self.headers, json=self.payload, timeout=self.timeout)
        response.raise_for_status()

        if self.debug: print('[AIRequest] send complete')
        return response

