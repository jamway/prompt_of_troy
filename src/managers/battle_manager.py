import csv
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime
from models.battle import Battle
from .prompt_manager import PromptManager
import logging

logger = logging.getLogger(__name__)

class BattleManager:
    def __init__(self, prompt_manager: PromptManager):
        """Initialize the BattleManager
        
        Args:
            prompt_manager: PromptManager instance for handling prompts
            
        Side effects:
            - Creates data directory if it doesn't exist
            - Initializes battles.csv if it doesn't exist
            - Loads existing battles from CSV
        """
        self.battles: Dict[str, Battle] = {}
        self.prompt_manager = prompt_manager
        self.csv_path = Path("data/battles.csv")
        self.init_storage()
        self.load_battles()
    
    def init_storage(self):
        """Initialize storage directory and CSV file
        
        Creates the data directory if it doesn't exist and initializes
        the CSV file with appropriate headers for battle data.
        
        CSV columns:
        - battle_id: Unique identifier for the battle
        - red_prompt: ID of the attacking prompt
        - blue_prompt: ID of the defending prompt
        - status: Current battle status (setup/completed)
        - time: Battle timestamp
        - winner: ID of the winning prompt
        - result: Dictionary containing battle results
        - secret_key: Secret key for the defense prompt
        - defense_prompt_with_key: Complete defense prompt with secret key
        """
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.csv_path.exists():
            with open(self.csv_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'battle_id', 'red_prompt', 'blue_prompt', 'status',
                    'time', 'winner', 'result', 'secret_key', 
                    'defense_prompt_with_key'
                ])
    
    def load_battles(self):
        """Load all battles from CSV file
        
        Reads the battles.csv file and creates Battle objects for each row.
        Handles potential errors during loading and logs relevant information.
        
        Side effects:
            - Populates self.battles dictionary
            - Logs loading status and any errors
        """
        if not self.csv_path.exists():
            return
            
        with open(self.csv_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                battle = Battle(
                    battle_id=row['battle_id'],
                    red_prompt=row['red_prompt'],
                    blue_prompt=row['blue_prompt'],
                    status=row['status'],
                    time=datetime.fromisoformat(row['time']),
                    winner=row['winner'],
                    result=eval(row['result']) if row['result'] else None,
                    secret_key=row['secret_key'],
                    defense_prompt_with_key=row['defense_prompt_with_key']
                )
                self.battles[battle.battle_id] = battle
    
    def save_battles(self):
        """Save all battles to CSV file
        
        Writes the current state of all battles to the CSV file.
        Includes error handling and maintains data consistency.
        
        Side effects:
            - Updates the battles.csv file with current battle data
            - Preserves battle history and results
        """
        with open(self.csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'battle_id', 'red_prompt', 'blue_prompt', 'status',
                'time', 'winner', 'result', 'secret_key', 
                'defense_prompt_with_key'
            ])
            for battle in self.battles.values():
                writer.writerow([
                    battle.battle_id,
                    battle.red_prompt,
                    battle.blue_prompt,
                    battle.status,
                    battle.time.isoformat(),
                    battle.winner,
                    str(battle.result) if battle.result else None,
                    battle.secret_key,
                    battle.defense_prompt_with_key
                ])
    
    def find_matching_opponents(self, prompt_id: str, num_opponents: int = 3) -> List[str]:
        """Find opponents with similar ELO ratings
        
        This function matches prompts based on their ELO ratings and ensures type compatibility
        (attack vs defense). It sorts potential opponents by rating difference to find the
        closest matches.
        
        Args:
            prompt_id: ID of the prompt seeking opponents
            num_opponents: Number of opponent IDs to return (default: 3)
            
        Returns:
            List of prompt IDs for the best matching opponents
            
        Raises:
            ValueError: If prompt_id is invalid or no compatible opponents are found
        """
        prompt = self.prompt_manager.prompts.get(prompt_id)
        if not prompt:
            raise ValueError("Invalid prompt ID")
            
        # Get all potential opponents of the opposite type
        opponent_type = "defense" if prompt.type == "attack" else "attack"
        potential_opponents = [
            p for p in self.prompt_manager.prompts.values()
            if p.type == opponent_type and p.id != prompt_id
        ]
        
        if not potential_opponents:
            raise ValueError(f"No {opponent_type} prompts available for battle")
            
        # Sort opponents by ELO rating difference
        sorted_opponents = sorted(
            potential_opponents,
            key=lambda x: abs(x.rating - prompt.rating)
        )
        
        # Return the N closest matches
        return [p.id for p in sorted_opponents[:num_opponents]]
    
    async def start_battle(self, red_prompt_id: str, blue_prompt_id: str = None) -> Battle:
        """Initialize a new battle between two prompts
        
        Sets up a battle between an attacking (red) and defending (blue) prompt.
        If no blue prompt is specified, automatically selects one with a similar rating.
        Ensures type compatibility and generates a secret key for the defense prompt.
        
        Args:
            red_prompt_id: ID of the attacking prompt
            blue_prompt_id: Optional ID of the defending prompt. If None, auto-selected
        
        Returns:
            Initialized Battle object ready for execution
            
        Raises:
            ValueError: If prompts are invalid or incompatible
        """
        red_prompt = self.prompt_manager.prompts.get(red_prompt_id)
        if not red_prompt:
            raise ValueError("Invalid red prompt ID")
            
        # Auto-select opponent if none specified
        if not blue_prompt_id:
            matching_opponents = self.find_matching_opponents(red_prompt_id, 1)
            if not matching_opponents:
                raise ValueError("No suitable opponents found")
            blue_prompt_id = matching_opponents[0]
            
        blue_prompt = self.prompt_manager.prompts.get(blue_prompt_id)
        if not blue_prompt:
            raise ValueError("Invalid blue prompt ID")
            
        # Verify prompt type compatibility
        if red_prompt.type == blue_prompt.type:
            raise ValueError("Prompts must be of different types")
            
        # Ensure red is attack and blue is defense
        if red_prompt.type != "attack":
            red_prompt_id, blue_prompt_id = blue_prompt_id, red_prompt_id
            red_prompt, blue_prompt = blue_prompt, red_prompt
        
        battle_id = f"battle_{len(self.battles)}"
        battle = Battle(
            battle_id=battle_id,
            red_prompt=red_prompt_id,
            blue_prompt=blue_prompt_id,
            status="setup"
        )
        
        # Setup Phase: Add secret key to defense prompt
        battle.setup_defense(blue_prompt.content)
        
        self.battles[battle.battle_id] = battle
        self.save_battles()
        
        return battle
    
    async def execute_battle(self, battle_id: str) -> Battle:
        """Execute a battle between attack and defense prompts
        
        This function orchestrates the battle execution process:
        1. Validates battle and prompt existence
        2. Executes the attack using LLM
        3. Evaluates if the attack succeeded in extracting the secret
        4. Updates battle results and ELO ratings
        
        Args:
            battle_id: Unique identifier of the battle to execute
            
        Returns:
            Updated Battle object with results
            
        Raises:
            ValueError: If battle not found or in invalid state
        """
        logger.info(f"Attempting to execute battle: {battle_id}")
        
        battle = self.battles.get(battle_id)
        if not battle:
            logger.error(f"Battle not found: {battle_id}")
            raise ValueError(f"Invalid battle ID: {battle_id}")
            
        if battle.status != "setup":
            logger.error(f"Invalid battle status: {battle.status}")
            raise ValueError(f"Battle {battle_id} not in setup phase, current status: {battle.status}")
        
        # Verify and retrieve prompts
        logger.info(f"Looking for prompts - Red: {battle.red_prompt}, Blue: {battle.blue_prompt}")
        logger.info(f"Available prompts: {list(self.prompt_manager.prompts.keys())}")
        
        red_prompt = self.prompt_manager.prompts.get(battle.red_prompt)
        blue_prompt = self.prompt_manager.prompts.get(battle.blue_prompt)
        
        if not red_prompt:
            logger.error(f"Red prompt not found: {battle.red_prompt}")
            raise ValueError(f"Red prompt not found: {battle.red_prompt}")
            
        if not blue_prompt:
            logger.error(f"Blue prompt not found: {battle.blue_prompt}")
            raise ValueError(f"Blue prompt not found: {battle.blue_prompt}")
            
        logger.info("Found both prompts:")
        logger.info(f"Red prompt: {red_prompt.id} - {red_prompt.content}")
        logger.info(f"Defense prompt with key: {battle.defense_prompt_with_key}")
        
        # Execution Phase: Run the attack
        from agent_utils.agent_utils import execute_battle_chat
        response = execute_battle_chat(
            attack_prompt=red_prompt.content,
            defense_prompt=battle.defense_prompt_with_key
        )
        
        # Evaluation Phase: Check if attack succeeded
        attack_wins = battle.evaluate_battle(response)
        
        # Update battle results
        battle.winner = battle.red_prompt if attack_wins else battle.blue_prompt
        battle.status = "completed"
        
        # Update prompt statistics and ELO ratings
        await self._update_battle_results(battle, attack_wins)
        
        self.save_battles()
        return battle
    
    async def _update_battle_results(self, battle: Battle, attack_wins: bool):
        """Update battle results and adjust ELO ratings
        
        Updates win/loss records and recalculates ELO ratings for both prompts.
        Uses standard ELO formula with K-factor of 32 for rating adjustments.
        
        Args:
            battle: Battle object containing the match details
            attack_wins: True if attacker won, False if defender won
            
        Returns:
            Updated battle object with final results
            
        Side effects:
            - Updates prompt win/loss records
            - Adjusts prompt ELO ratings
            - Saves updated data to CSV files
        """
        red_prompt = self.prompt_manager.prompts[battle.red_prompt]
        blue_prompt = self.prompt_manager.prompts[battle.blue_prompt]
        
        # Update win/loss records
        if attack_wins:
            red_prompt.battles_won += 1
            blue_prompt.battles_lost += 1
        else:
            blue_prompt.battles_won += 1
            red_prompt.battles_lost += 1
        
        # Calculate ELO rating changes
        k_factor = 32  # Standard chess K-factor
        red_expected = 1 / (1 + 10**((blue_prompt.rating - red_prompt.rating)/400))
        red_actual = 1 if attack_wins else 0
        
        # Apply ELO adjustments
        red_prompt.rating += k_factor * (red_actual - red_expected)
        blue_prompt.rating += k_factor * ((1-red_actual) - (1-red_expected))
        
        # Save updated prompt data
        self.prompt_manager.update_prompt(red_prompt)
        self.prompt_manager.update_prompt(blue_prompt)
        
        # Record battle results
        battle.result = {
            'winner': battle.winner,
            'attack_wins': attack_wins,
            'secret_key': battle.secret_key,
            'rating_change': {
                battle.red_prompt: k_factor * (red_actual - red_expected),
                battle.blue_prompt: k_factor * ((1-red_actual) - (1-red_expected))
            }
        }
        battle.status = "completed"
        
        self.battles[battle.battle_id] = battle
        self.save_battles()
        
        return battle

    def get_battle_status(self, battle_id: str) -> Optional[Battle]:
        """Get the current status of a battle
        
        Args:
            battle_id: ID of the battle to check
            
        Returns:
            Battle object if found, None otherwise
            
        Example:
            >>> battle = battle_manager.get_battle_status("battle_0")
            >>> if battle:
            ...     print(f"Status: {battle.status}")
            ...     if battle.status == "completed":
            ...         print(f"Winner: {battle.winner}")
        """
        return self.battles.get(battle_id)