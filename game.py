import json
import random
import datetime
import os

DATA_FILE = "learning_data.json"

class LearningPlatform:
    def __init__(self):
        self.load_data()
    
    def load_data(self):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r") as f:
                self.data = json.load(f)
        else:
            self.data = {"flashcards": [], "daily_challenge_count": {}, "scores": {}}

    def save_data(self):
        with open(DATA_FILE, "w") as f:
            json.dump(self.data, f, indent=4)
    
    def add_flashcard(self):
        question = input("Enter the question: ")
        answer = input("Enter the answer: ")
        self.data["flashcards"].append({"question": question, "answer": answer})
        self.save_data()
        print("Flashcard added successfully!\n")
    
    def generate_options(self, correct_answer):
        all_answers = [fc["answer"] for fc in self.data["flashcards"] if fc["answer"] != correct_answer]
        random.shuffle(all_answers)
        options = random.sample(all_answers, min(3, len(all_answers))) + [correct_answer]
        random.shuffle(options)
        return options
    
    def review_game(self):
        if not self.data["flashcards"]:
            print("No flashcards available. Add some first!\n")
            return
        
        score = 0
        flashcards = self.data["flashcards"][:]
        random.shuffle(flashcards)
        
        for flashcard in flashcards:
            print("\nQuestion:", flashcard["question"])
            options = self.generate_options(flashcard["answer"])
            for i, opt in enumerate(options):
                print(f"{i+1}. {opt}")
            
            try:
                choice = int(input("Choose the correct option (1-4): "))
                if options[choice - 1] == flashcard["answer"]:
                    print("Correct!\n")
                    score += 1
                else:
                    print(f"Wrong! The correct answer is: {flashcard['answer']}\n")
            except (ValueError, IndexError):
                print("Invalid input! Skipping question.\n")
        
        print(f"Game Over! Your Score: {score}/{len(self.data['flashcards'])}\n")
    
    def daily_challenge(self):
        today = str(datetime.date.today())
        if today not in self.data["daily_challenge_count"]:
            self.data["daily_challenge_count"][today] = 0
        
        if self.data["daily_challenge_count"][today] >= 3:
            print("You've reached the maximum attempts for today. Try again tomorrow!\n")
            return
        
        print("Daily Challenge: Write your answers for the following questions.")
        score = 0
        penalty = 0
        
        flashcards = self.data["flashcards"][:]
        random.shuffle(flashcards)
        
        for flashcard in flashcards:
            print("\nQuestion:", flashcard["question"])
            user_answer = input("Your Answer: ")
            
            grading_result = self.grade_answer(user_answer, flashcard["answer"])
            print(f"Grading Result: {grading_result}/5")
            penalty += (5 - grading_result)
            
            if penalty >= 10:
                print("Game Over! Too many incorrect answers.")
                break
        
        self.data["daily_challenge_count"][today] += 1
        self.save_data()
    
    def grade_answer(self, user_answer, correct_answer):
        # Placeholder for AI grading logic, here we use a simple similarity check
        correct_words = set(correct_answer.lower().split())
        user_words = set(user_answer.lower().split())
        score = int((len(user_words & correct_words) / max(1, len(correct_words))) * 5)
        return max(0, min(5, score))

    def main_menu(self):
        while True:
            print("\n=== Learning Platform ===")
            print("1. Add Flashcard")
            print("2. Review Game")
            print("3. Daily Challenge")
            print("4. Exit")
            choice = input("Select an option: ")
            
            if choice == "1":
                self.add_flashcard()
            elif choice == "2":
                self.review_game()
            elif choice == "3":
                self.daily_challenge()
            elif choice == "4":
                print("Exiting the platform. Goodbye!")
                break
            else:
                print("Invalid choice. Please select again.")

if __name__ == "__main__":
    platform = LearningPlatform()
    platform.main_menu()
