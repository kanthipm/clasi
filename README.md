# CLASI – Your Schedule Solution

## Team Members
Alan Qiao, Camden Chin, Kanthi Makineedi, Advait Bhaskar Pandit, Julia Healey-Parera

## Description
Clasi is an interactive course recommendation tool designed to streamline Duke students' class selection process. By balancing major requirements, graduation codes, GPA goals, and personal interests, Clasi helps students, especially first-years, make informed scheduling decisions.

Users can customize recommendations based on:
- **Academic Filters**: Area of Knowledge codes, Methods of Inquiry tags, major-specific courses.
- **Professor Preferences**: Names, ratings, difficulty levels (web scraped from RateMyProfessor).
- **Logistics**: Preferred campus locations, class times, and schedule constraints.
- **Positive & Negative Selection**: Users can specify desired or avoided class attributes.

## Features
- **Course Data Scraper** – Extracts up-to-date class listings from DukeHub using a headless browser.  
- **Professor Rating Integration** – Collects and integrates professor ratings and reviews.  
- **Advanced Search & Ranking** – Users can filter by department, prerequisites, professor preferences, and logistics.  
- **User Authentication** – Save favorite courses, schedules, and professors.  
- **Dynamic Course Recommendations** – Ranked suggestions based on user-defined parameters.  
- **Vector Database for Course Matching** – Aligns student inputs with course attributes for intelligent recommendations.  
- **AI-Driven Class Suggestions** – Predicts enjoyment based on past class ratings and teaching styles.  
- **Schedule Generator** – Uses a greedy algorithm to create conflict-free schedules.  

### **Course Search Page**
This page allows students to search for courses, filter by various parameters, and view class details.
![image](https://github.com/user-attachments/assets/983f5a4c-aecb-4fdb-a42c-82db29b9b51b)

### **Course Detail Page**
A detailed view of a course, including professor ratings, reviews, prerequisites, and an option to write a review.
![image](https://github.com/user-attachments/assets/2bb42b68-b60d-417b-bbf0-3710c4b27265)

## Installation

### 1️⃣ Clone the Repository
```sh
git clone https://github.com/your-username/clasi.git
cd clasi
