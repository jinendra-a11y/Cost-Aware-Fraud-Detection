import difflib

string1 = "Arriva"
string2 = "Arriva Inc"

print(difflib.SequenceMatcher(None, str(string1).lower().strip(), str(string2).lower().strip()).ratio())