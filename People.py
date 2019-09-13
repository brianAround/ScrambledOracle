
class Person:

    recognized_pronouns = ['he','she','thee','i','we','they','thou']

    def __init__(self):
        self.names = {}
        self.nouns = {}
        self.pronouns = {}
        self.adjectives = {}

    def matches_word(self, word):
        strength = 0
        if word in self.names:
            strength = 1 / len(self.names)
        elif word.lower() in self.nouns:
            strength = 1 / len(self.nouns)
        elif len([noun for noun in self.nouns if word.lower() in noun or noun in word.lower()]) > 0:
            for noun in self.nouns:
                if len(noun) != len(word):
                    if len(noun) < len(word):
                        small_word = noun
                        big_word = word
                    else:
                        small_word = word
                        big_word = noun
                    new_strength = len(small_word) / len(big_word)
                    strength = max(new_strength, strength)
        elif word.lower() in self.pronouns:
            strength = 0.25
        elif word.lower() in self.adjectives:
            strength = 0.25
        return strength

    def __str__(self):
        result = '(Person: ' + ' '.join([name for name in self.names]) \
                 + (' pronouns: ' + ",".join([word for word in self.pronouns]) if len(self.pronouns) > 0 else '') \
                 + (' nouns: ' + ",".join([noun for noun in self.nouns]) if len(self.nouns) > 0 else '') \
                 + (' adjectives: ' + ','.join([word for word in self.adjectives]) if len(self.adjectives) > 0 else '') \
                 + ')'
        return result

    def matches_phrase(self, words:list):
        return sum([self.matches_word(this_word) for this_word in words])

    def add_name(self, word:str):
        if word not in self.names:
            self.names[word] = 1

    def add_noun(self, word:str):
        word = word.lower()
        if word not in self.nouns:
            if word in self.recognized_pronouns:
                self.add_pronoun(word)
            else:
                self.nouns[word] = 1

    def add_pronoun(self, word:str):
        word = word.lower()
        if word in self.recognized_pronouns and word not in self.pronouns:
            self.pronouns[word] = 1

    def say_person(self):
        if len(self.names) > 0:
            return ' '.join(self.names)
        if len(self.nouns) > 0:
            return self.nouns[0]
        if len(self.pronouns) > 0:
            return self.pronouns[0]
        return 'person'



class People(list):

    def find_word_matches(self, word:str):
        return self.find_phrase_matches([word])

    def find_phrase_matches(self, words:list):
        results = []
        for this_person in self:
            current_score = this_person.matches_phrase(words)
            if current_score != 0:
                results.append([this_person, current_score])
        return sorted(results, key=lambda x: x[1], reverse=True)

    def has_match(self, word:str, min_strength:int=0.25):
        return len([match for match in self.find_word_matches(word) if match[1] >= min_strength]) > 0

    def append(self, object:Person):
        if object in self:
            self.remove(object)
        super().append(object)

    def insert(self, index: int, object:Person):
        super().insert(index, object)

    def index(self, object: Person, start: int = 0, stop: int = ...):
        super().index(object, start, stop)

    def add_name(self, name:str):
        possible_matches = self.find_word_matches(name)
        exact_match = None
        for entry in possible_matches:
            if name in entry[0].names:
                exact_match = entry[0]
                break
        if exact_match is None:
            new_person = Person()
            new_person.add_name(name)
            self.append(new_person)

    def add_noun(self, noun:str):
        possible_matches = self.find_word_matches(noun)
        exact_match = None
        for entry in possible_matches:
            if noun in entry[0].nouns:
                exact_match = entry[0]
                break
        if exact_match is None:
            new_person = Person()
            new_person.add_noun(noun)
            self.append(new_person)


if __name__ == "__main__":
    people = People()
    people.add_name('Brian')
    people.add_name('Laura')
    people.add_name('Brian')

    for person in people:
        print(person)