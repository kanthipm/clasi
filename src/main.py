# src/main.py
from .dropdown_items import term_list, subj_list, acad_car_list

def main():
    subjects = subj_list()
    terms = term_list()
    acad_car = acad_car_list()
    print(terms)

if __name__ == "__main__":
    main()  
