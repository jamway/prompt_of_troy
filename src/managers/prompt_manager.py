import csv
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime
from models.prompt import Prompt
import logging

logger = logging.getLogger(__name__)

class PromptManager:
    def __init__(self, csv_path: str = "data/prompts.csv"):
        """Initialize the PromptManager
        
        Args:
            csv_path: Path to the CSV file for storing prompts (default: "data/prompts.csv")
        """
        self.csv_path = Path(csv_path)
        self.prompts: Dict[str, Prompt] = {}
        self.init_storage()
        self.load_prompts()
    
    def init_storage(self):
        """Initialize storage directory and CSV file
        
        Creates the data directory if it doesn't exist and initializes
        the CSV file with appropriate headers.
        """
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.csv_path.exists():
            with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'user_id', 'type', 'code_name', 'content', 
                    'created_at', 'battles_won', 'battles_lost', 'rating'
                ])
    
    def load_prompts(self):
        """Load all prompts from CSV file
        
        Reads the CSV file and creates Prompt objects for each row.
        Handles potential errors during loading and logs relevant information.
        
        Side effects:
            - Populates self.prompts dictionary
            - Logs loading status and any errors
        """
        if not self.csv_path.exists():
            return
            
        try:
            with open(self.csv_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        prompt = Prompt(
                            user_id=row['user_id'],
                            type=row['type'],
                            code_name=row['code_name'],
                            content=row['content'],
                            created_at=datetime.fromisoformat(row['created_at']),
                            battles_won=int(row['battles_won']),
                            battles_lost=int(row['battles_lost']),
                            rating=int(row['rating'])
                        )
                        self.prompts[prompt.id] = prompt
                        logger.info(f"Loaded prompt: {prompt.id}")
                    except Exception as e:
                        logger.error(f"Failed to load prompt from row: {row}", exc_info=True)
                        
            logger.info(f"Loaded {len(self.prompts)} prompts")
            logger.info(f"Available prompts: {list(self.prompts.keys())}")
        except Exception as e:
            logger.error(f"Failed to load prompts from CSV: {str(e)}", exc_info=True)
    
    def save_prompts(self):
        """Save all prompts to CSV file
        
        Writes the current state of all prompts to the CSV file.
        Includes error handling and logging.
        
        Side effects:
            - Updates the CSV file with current prompt data
            - Logs save status and any errors
        """
        try:
            with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'user_id', 'type', 'code_name', 'content', 
                    'created_at', 'battles_won', 'battles_lost', 'rating'
                ])
                for prompt in self.prompts.values():
                    writer.writerow([
                        prompt.user_id,
                        prompt.type,
                        prompt.code_name,
                        prompt.content,
                        prompt.created_at.isoformat(),
                        prompt.battles_won,
                        prompt.battles_lost,
                        prompt.rating
                    ])
            logger.info(f"Saved {len(self.prompts)} prompts to CSV")
        except Exception as e:
            logger.error(f"Failed to save prompts to CSV: {str(e)}", exc_info=True)
    
    def create_prompt(self, user_id: str, type: str, code_name: str, content: str) -> Prompt:
        """Create a new prompt
        
        Creates a new Prompt object with initial values and saves it to storage.
        
        Args:
            user_id: Discord user ID of the prompt creator
            type: Type of prompt ("attack" or "defense")
            code_name: User-defined name for the prompt
            content: The actual prompt text
            
        Returns:
            Newly created Prompt object
            
        Side effects:
            - Adds prompt to self.prompts dictionary
            - Saves updated data to CSV
        """
        prompt = Prompt(
            user_id=user_id,
            type=type,
            code_name=code_name,
            content=content,
            created_at=datetime.now()
        )
        self.prompts[prompt.id] = prompt
        logger.info(f"Created new prompt: {prompt.id}")
        self.save_prompts()
        return prompt
    
    def delete_prompt(self, prompt_id: str) -> bool:
        """Delete a prompt
        
        Args:
            prompt_id: ID of the prompt to delete
            
        Returns:
            True if prompt was deleted, False if not found
            
        Side effects:
            - Removes prompt from self.prompts dictionary if found
            - Saves updated data to CSV if deletion successful
        """
        if prompt_id in self.prompts:
            del self.prompts[prompt_id]
            logger.info(f"Deleted prompt: {prompt_id}")
            self.save_prompts()
            return True
        logger.warning(f"Attempt to delete non-existent prompt: {prompt_id}")
        return False
    
    def list_prompts(self, user_id: Optional[str] = None, type: Optional[str] = None) -> List[Prompt]:
        """List prompts with optional filtering
        
        Args:
            user_id: Optional filter by user ID
            type: Optional filter by prompt type ("attack" or "defense")
            
        Returns:
            List of Prompt objects matching the filters
        """
        prompts = self.prompts.values()
        if user_id:
            prompts = [p for p in prompts if p.user_id == user_id]
        if type:
            prompts = [p for p in prompts if p.type == type]
        return list(prompts)
    
    def update_prompt(self, prompt: Prompt):
        """Update an existing prompt
        
        Args:
            prompt: Updated Prompt object
            
        Side effects:
            - Updates prompt in self.prompts dictionary
            - Saves updated data to CSV
        """
        self.prompts[prompt.id] = prompt
        logger.info(f"Updated prompt: {prompt.id}")
        self.save_prompts()
    
    def get_prompt(self, prompt_id: str) -> Optional[Prompt]:
        """Get a specific prompt by ID
        
        Args:
            prompt_id: ID of the prompt to retrieve
            
        Returns:
            Prompt object if found, None otherwise
            
        Side effects:
            - Logs warning if prompt not found
        """
        if prompt_id not in self.prompts:
            logger.warning(f"Prompt not found: {prompt_id}")
        return self.prompts.get(prompt_id)