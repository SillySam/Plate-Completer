import requests
import json
import bs4
from bs4 import BeautifulSoup

''' Read and expand plates stored in JSON '''
def get_plate_prefixes():

    generated_prefixs = {
        # year: [list of prefixes]
        # eg/
        #   2016:['ABC', 'ABD'...]
    }

    with open('plate_prefixs.json') as json_file:
        data = json.load(json_file)
        for year, plate_list in data.items():

            expanded_plates = []

            for item in plate_list:
                if '-' in item: # Plate is a range, eg ABC - ABF
                    expanded_plates += expand_plate_range(item)
                else:           # Plate is singular
                    expanded_plates.append(item)

            generated_prefixs.update({year:expanded_plates})

    return generated_prefixs

''' Expand Plate Range (eg: AAA-ZZZ)'''
def expand_plate_range(plate):
    plates = []

    plate = plate.upper()
    start, end = plate.split('-')
    start, end = list(start), list(end)

    while True:

        plates.append(''.join(start))
        if start == end: break # list is fully generated

        ''' Alphabetically iterate downwards (A-Z) for each
            character in list, eg: AAA -> AAB -> AAC. Once
            the last char is Z, reset to A and increase 
            alphabetical value of letter before. If all
            letters equal to ending range, or 'Z',
            generation is complete. '''

        if(start[len(start)-1] == 'Z'): 

            if(start[len(start)-2] == 'Z'):
                start[len(start)-2] = 'A'
                start[len(start)-3] = chr(ord(start[len(start)-3]) + 1)
            
            else:
                start[len(start)-2] = chr(ord(start[len(start)-2]) + 1)
            start[len(start)-1] = 'A'

        else:
            start[len(start)-1] = chr(ord(start[len(start)-1]) + 1)

    return plates           

''' Get all prefixes that could be in the provided plate'''
def match_prefix(patchy_plate):
    possible_prefixes = {}
    plate_start = patchy_plate[:3]
    plates = get_plate_prefixes()

    if plate_start.replace('?','') != '': # anything unknown to find?

        for year, prefixes in plates.items():
            for prefix in prefixes:
                is_match = True

                # Go through each char of plate start (eg 'ABC')
                for i in range(len(prefix)):
                    # Check if char at current index is known 
                    if plate_start[i] != "?":
                        # Does this char match the possible prefix?
                        if plate_start[i] != prefix[i]:
                            is_match = False # No match

                if is_match:
                    if len(prefix) == 2 and plate_start[2].isalpha():
                        pass # plate is 3 chars long but the one matched
                             # is a 2 char old plate
                    else:
                        # Format into dictionary by year:plates[]
                        if year in possible_prefixes:
                            possible_prefixes[year].append(prefix)
                        else:
                            possible_prefixes[year] = [prefix]
    else: 
        # no prefix, return all
        possible_prefixes = plates

    return possible_prefixes

''' Form a list of number combonations with a plate '''
def generate_number_combos(plate_end):
    solutions = []

    # Get indexes of unknown numbers
    q_indexes = [i for i, ltr in enumerate(plate_end) if ltr == '?']
    number_of_q = len(q_indexes)

    # Generate list of number combos
    nums = [((("0" * (number_of_q - len(str(i)))) + str(i))) for i in range(0, 10 ** number_of_q)]

    # Use generated nums by replacing the unknown '?'s
    for i in nums:
        current = list(plate_end)

        # Replace '?' with number possibilities
        for j in range(len(q_indexes)):
            current[q_indexes[j]] = i[j]

        solutions.append(''.join(current))

    return solutions

''' Gathers prefix's and endings to create a list of possible plates '''
def get_possible_plates(partial_plate):
    
    prefixes = match_prefix(plate) 

    # Calculate how many letters at the start
    prefix_length = 3
    if len(prefixes) > 0:
        if len(prefixes[list(prefixes)[0]][0]) == 2:
            prefix_length = 2

    # Get ending and generate number combos
    end = plate[prefix_length:]
    ending_numbers = generate_number_combos(end)

    possibilities = []
    years  = []

    # Generate possiblities by mixing prefixes with ending numbers
    for year, pre in prefixes.items():
        if year not in years:
            years.append(year)

        for p in pre:
            for nums in ending_numbers:
                possibilities.append('{}{}'.format(p,nums))
    
    # Print year possibilites (according to prefix json)
    for y in years:
        print('[!] Year Possibility:', y)

    return possibilities
    
if __name__ == "__main__":
    print('[ NZ Plate Finder ]')
    print('[?] This tool does NOT support custom plates!\n')

    plate = input("Enter Plate (eg: E?T42?): ")

    possibilities = get_possible_plates(plate)
    amount_of_possibilities = len(possibilities)

    print('[!] # of possibilities:', amount_of_possibilities)

    if amount_of_possibilities < 1:
        print('That looks like an invalid plate!')
        print('If the plate is valid, please report an issue!')
        exit(1)

    # output
    print("outputting", amount_of_possibilities, " possibilities")
    print('saving to plates.txt')
    file_ = open('plates.txt', 'w')
    file_.write(str(possibilities))
    file_.close()

    # Do something with these generated possible plates ...
