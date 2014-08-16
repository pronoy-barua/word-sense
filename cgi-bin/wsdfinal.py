#!/usr/bin/env python

import cgi
import cgitb; cgitb.enable()  # for troubleshooting
import sys
import nltk
from nltk.corpus import wordnet


print "Content-type: text/html"
print


print """
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Word Sense Disambiguation</title>
    <link rel="stylesheet" href="bootstrap.min.css">
  </head>			
"""

    
def is_stopword(string):
  if string.lower() in nltk.corpus.stopwords.words('english'):
    return True
  else:
    return False
    
def is_punctuation(string):
  for char in string:
    if char.isalpha() or char.isdigit():
      return False
  return True
  
  
def wordnet_pos_code(tag):
  if tag.startswith('NN'):
    return wordnet.NOUN
  elif tag.startswith('VB'):
    return wordnet.VERB
  elif tag.startswith('JJ'):
    return wordnet.ADJ
  elif tag.startswith('RB'):
    return wordnet.ADV
  else:
    return ''
    
    
def wordnet_pos_label(tag):
  if tag.startswith('NN'):
    return "Noun"
  elif tag.startswith('VB'):
    return "Verb"
  elif tag.startswith('JJ'):
    return "Adjective"
  elif tag.startswith('RB'):
    return "Adverb"
  else:
    return tag
    
    
def wordnet_definitions(sentence):
  wnl = nltk.WordNetLemmatizer()
  for token in sentence:
    word = token['word']
    wn_pos = wordnet_pos_code(token['pos'])
    if is_punctuation(word):
      token['punct'] = True
    elif is_stopword(word):
      pass
    elif len(wordnet.synsets(word, wn_pos)) > 0:
      token['wn_lemma'] = wnl.lemmatize(word.lower())
      token['wn_pos'] = wordnet_pos_label(token['pos'])
      defs = [sense.definition for sense in wordnet.synsets(word, wn_pos)]
      token['wn_def'] = "; \n".join(defs) 
    else:
      pass
  return sentence
  
def longest_common_substring(s1, s2):
  m = [[0] * (1+len(s2)) for i in xrange(1 + len(s1))]
  longest, x_longest = 0,0
  for x in xrange(1, 1 + len(s1)):
    for y in xrange(1, 1 + len(s2)):
      if s1[x - 1] == s2[y - 1]:
        m[x][y] = m[x-1][y-1] + 1
        if m[x][y] > longest:
          longest = m[x][y]
          x_longest = x
      else:
        m[x][y] = 0
  return s1[x_longest - longest: x_longest]

# compares the pos for preceding word in the examples
# with the one in the sentence
def pos_disambiguate(word, marked_str, word_pos):
  max_length = len(word_pos) + 3
  senses = []
  for synset in wordnet.synsets(word):
    for example in synset.examples:
      tokens = nltk.word_tokenize(example)
      tag_tuples = nltk.pos_tag(tokens)
      word_index = [i for i, j in enumerate(tokens) if j==word]
      if len(word_index) > 0:
        ex_mark_pos = []
        for i in range(len(tokens)):
          if i == word_index[0]:
            ex_mark_pos.append(word_pos)
          else:
            ex_mark_pos.append(tag_tuples[i][1])
        ex_marked_str = '-'+'-'.join(ex_mark_pos)+'-'
      else:
        continue
      #marked pos string generated for example
      lcs_str = longest_common_substring(marked_str,ex_marked_str)
      if (word_pos in lcs_str) and (len(lcs_str) >= max_length):
        senses.append(synset.definition)
        max_length = len(lcs_str)
        break
        
      
  if len(senses) > 1:
    return senses
  return 0
  

  
def word_sense_disambiguate(word, wn_pos, sentence):
  senses = wordnet.synsets(word, wn_pos)
  cfd = nltk.ConditionalFreqDist(
             (sense, def_word)
             for sense in senses
             for def_word in sense.definition.split())
             #if def_word in sentence)
  best_sense = senses[0] # start with first sense
  for sense in senses:
    if cfd[sense].max() > cfd[best_sense].max():
      best_sense = sense
  return best_sense
  
def main():

  form = cgi.FieldStorage()
    
  index = int(form.getvalue("index",-1))
  sent = form.getvalue("sent","default")
  
  tokens = nltk.word_tokenize(sent)
  tag_tuples = nltk.pos_tag(tokens)
  sentence = []
  for (string, tag) in tag_tuples:
    token = {'word':string, 'pos':tag}
    sentence.append(token)
  sent_def = wordnet_definitions(sentence)
  word = sent_def[index]['word']
  wn_pos = wordnet_pos_code(sent_def[index]['pos'])
  word_pos = 'WORD'
  
  #mark the POS tag of the word and generate POS string
  #to check if the longest common substring contains the word
  mark_pos = []
  for i in range(len(sent_def)):
    if i == index:
      mark_pos.append(word_pos)
    else:
      mark_pos.append(sent_def[i]['pos'])
      
  marked_str = '-'+'-'.join(mark_pos)+'-'
 
  senses = pos_disambiguate(word, marked_str, word_pos)
  if senses != 0:
    output = '\n\n'.join(senses)
  else:  
    output = word_sense_disambiguate(word, wn_pos, sent_def).definition
  

  
  print """
    <p class="sentence">Sentence : %s</p>
    <p class="index">Index : %s</p>
		<p class="sense">Best Sense : %s</p>
	  </body>
	  </html>
  """%(sent, index,output)
  
if __name__ == '__main__':
  main()
