from dataclasses import dataclass
from datetime import datetime

@dataclass
class Prompt:
    """A class representing a prompt for prompt battles
    
    Attributes:
        user_id (str): Discord user ID of the prompt creator
        type (str): Type of prompt ("attack" or "defense") 
        code_name (str): User-defined name for the prompt
        content (str): The actual prompt text
        created_at (datetime): Timestamp when prompt was created
        battles_won (int): Number of battles this prompt has won
        battles_lost (int): Number of battles this prompt has lost
        rating (int): ELO rating for matchmaking, starts at 1500
    """
    user_id: str
    type: str
    code_name: str
    content: str
    created_at: datetime
    battles_won: int = 0
    battles_lost: int = 0
    rating: int = 1500  # Initial ELO rating
    
    @property
    def id(self) -> str:
        """Generate a unique identifier for the prompt
        
        Returns:
            str: Unique ID in format "@user_id/type/code_name"
        """
        return f"@{self.user_id}/{self.type}/{self.code_name}"
    
    @property
    def win_rate(self) -> float:
        """Calculate win rate as a percentage
        
        Returns:
            float: Win rate percentage from 0-100, or 0 if no battles
        """
        total = self.battles_won + self.battles_lost
        return (self.battles_won / total * 100) if total > 0 else 0
    
    def to_dict(self) -> dict:
        """Convert prompt to dictionary for storage
        
        Returns:
            dict: Dictionary containing all prompt attributes
        """
        return {
            "user_id": self.user_id,
            "type": self.type,
            "code_name": self.code_name,
            "content": self.content,
            "created_at": self.created_at.isoformat(),
            "battles_won": self.battles_won,
            "battles_lost": self.battles_lost,
            "rating": self.rating
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Prompt":
        """Create prompt from dictionary data
        
        Args:
            data (dict): Dictionary containing prompt attributes
            
        Returns:
            Prompt: New Prompt instance initialized with data
        """
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)