# HTML-Diff: HTML-formatted diff'ing of HTML snippets

Compares two HTML snippets strings and returns the diff as a valid HTML snippet with changes wrapped in `<diff:delete>` and `<diff:insert>` tags. 

The tags are referred to by their old names `<del>` and `<ins>` in the description below.

Relies on `BeautifulSoup4` with `html.parser` backend for HTML parsing and dumping.

HTML-Diff focusses on providing *valid* diffs, that is:

1. The returned strings represent valid HTML snippets;
2. Provided that the input snippets represent valid HTML snippets containing no `<del>` or `<ins>` tags, they can be identically reconstructed from the diff output, by removing `<ins>` tags and their content and replacing `<del>` tags by their content for the *old* snippet, the other way round for the *new* one. Functions are provided in the `check` module for those reconstructions and checking that the reconstructions match the inputs.


## Usage

### Basic usage

```python
>>> from html_diff import diff
>>> diff("<em>ABC</em>", "<em>AB</em>C")
'<em><del>ABC</del><ins>AB</ins></em><ins>C</ins>'
```


### Adding custom tags to be treated as insecable blocks

Example use case: having MathJax elements wrapped into `<span class="math-tex">\(...\)</span>` and wanting to avoid `<del>` and `<ins>` tags inside the `\(...\)` (which would be badly rendered):

```python
>>> from html_diff.config import config
>>> config.tags_fcts_as_blocks.append(lambda tag: tag.name == "span" and "math-tex" in tag.attrs.get("class", []))
```

Without it (does not render correctly with MathJax):

```python
>>> diff(r'<span class="math-tex">\(\vec{v}\)</span>', r'<span class="math-tex">\(\vec{w}\)</span>')
'<span class="math-tex">\\(\\vec{<del>v</del><ins>w</ins>}\\)</span>'
```

With it:

```python
>>> from html_diff import clear_cache
>>> clear_cache()
>>> diff(r'<span class="math-tex">\(\vec{v}\)</span>', r'<span class="math-tex">\(\vec{w}\)</span>')
'<del><span class="math-tex">\\(\\vec{v}\\)</span></del><ins><span class="math-tex">\\(\\vec{w}\\)</span></ins>'
```

The functions in `config.config.tags_fcts_as_blocks` should take a `bs4.element.Tag` as input and return a `bool`; the tags are tested against all functions in the list, and are considered insecable blocks if any call returns `True`.


### Score for tags

HTML tags have a base score associated, which is added to there content score. This base score can be configured:

```python
>>> config.EMPTY_ELEMENT_SCORE # default: 2
>>> config.OTHER_ELEMENT_SCORE # default: 2
```

WARNING: some results are cached and changing the config does not invalidate the cache, thus the results may be wrong afterwards. Call `clear_cache()` to reset the cache.


### Reconstructing *old* and *new* from *diff*

```python
>>> old = "old_string"
>>> new = "new_string"
>>> d = diff(old, new)
>>> from html_diff.check import new_from_diff
>>> new == new_from_diff(d)
True
>>> from html_diff.check import old_from_diff
>>> old == old_from_diff(d)
True
>>> from html_diff.check import is_diff_valid
>>> is_diff_valid(old, new, d)
True
```


## Testing

### Automated testing

Run

```bash
python -m unittest
```

at the root of the project.


### Manual testing

Run

```bash
python -m html_diff
```

and navigate to 127.0.0.1:8080 with your browser.

You can specify further options:

- `-a` or `--address`: custom address of the server (default: 127.0.0.1)
- `-p` or `--port`: custom port of the server (default: 8080)
- `-b` or `--blocks`: definitions of functions to be added to `config.config.tags_fcts_as_blocks`, e.g.:

```bash
python -m html_diff -b 'lambda tag: tag.name == "span" and "math-tex" in tag.attrs.get("class", [])'
```

- `-c` or `--cuttable-words-mode`: way of treating words cutting, see above for details; one of the `config.Config.CuttableWordsMode` values (default: CUTTABLE)


## Algorithm

The new implementation uses an algorithm that is closer to `difflib.SequenceMatcher`, although it does ironically not use it anymore.

The algorithm is similar to the legacy implementation with the `UNCUTTABLE_PRECISE` configuration, with the difference that it uses a Ratcliff-Obershelp-like procedure (best-matching subsequence) on all levels rather than testing all combinations to find the optimum. It is thus faster.


### Matching

1. Parse the inputs with `BeautifulSoup4`; this yields two iterables of elements, either `bs4.element.NavigableString` or `bs4.element.Tag`.
2. On the top level of the HTML structure, split the `bs4.element.NavigableString`'s in words (using `re`'s `\W` pattern), then find the best-matching subsequence, using a score:
	- identical words: the length of the word,
	- `bs4.element.Tag`'s where the `name` and `attrs` attributes match exactly:
		- if the tags are considered as blocks (those that test `True` with a function of `config.config.tags_fcts_as_blocks`): `config.EMPTY_ELEMENT_SCORE` if the tags are *empty*, else `config.OTHER_ELEMENT_SCORE` plus the length of the string content of the tags,
		- else, `config.OTHER_ELEMENT_SCORE` plus the sum of the scores of the tags' contents (calculated recursively).
3. On the left and the right of the best-matching subsequence, repeat 2. If non-matchable subsequences remain, assign them a score of 0 and treat them as completely deleted/inserted.


### Dumping

4. With those tree match structures, dumping can be done directly, recursively, by dumping the `node_left` first, then the matched subsequence, finally the `node_right`. Matches are always exact and thus can be dumped as-is, except for non-matchables subsequences that are first completely deleted and then completely reinserted.
5. Dumping is done in a `BeautifulSoup4` soup, then output as a string.


## Legacy implementation

The legacy implementation is available in `html_diff.legacy`.


### Word cutting in diff

By default, the diff'ing algorithm for plain text parts does not care about words - if a word part is modified, that part gets `<del>`'ed and `<ins>`'ed, while the rest of the word remains untouched. It may however be more readable to have full words deleted and reinserted. To ensure this, switch `config.config.cuttable_words_mode` to either `config.Config.CuttableWordsMode.UNCUTTABLE_SIMPLE` or `config.Config.CuttableWordsMode.UNCUTTABLE_PRECISE`:


`config.config.cuttable_words_mode == config.Config.CuttableWordsMode.CUTTABLE` (default):

```python
>>> from html_diff.legacy import diff as ldiff
>>> ldiff("OlyExams", "ExamTools")
'<del>Oly</del>Exam<ins>Tool</ins>s'
>>> ldiff("abcdef<br/>ghifjk", "abcdef ghifjk")
'abcdef<ins> ghifjk</ins><del><br/>ghifjk</del>'
```

`config.config.cuttable_words_mode == config.Config.CuttableWordsMode.UNCUTTABLE_SIMPLE` (fast and gives acceptable results):

```python
>>> ldiff("OlyExams", "ExamTools")
'<del>OlyExams</del><ins>ExamTools</ins>'
>>> ldiff("abcdef<br/>ghifjk", "abcdef ghifjk")
'abcdef<ins> ghifjk</ins><del><br/>ghifjk</del>'
```

`config.config.cuttable_words_mode == config.Config.CuttableWordsMode.UNCUTTABLE_PRECISE` (quite slow, but uses early word breaking for better matching, in particular if plain string parts of the inputs were split or merged between *old* and *new*):

```python
>>> ldiff("OlyExams", "ExamTools")
'<del>OlyExams</del><ins>ExamTools</ins>'
>>> ldiff("abcdef<br/>ghifjk", "abcdef ghifjk")
'abcdef<del><br/></del><ins> </ins>ghifjk'
```

In uncuttable words modes, non-word characters correspond to `re`'s `\W` pattern.


### Algorithm

#### Matching

1. Parse the inputs with `BeautifulSoup4`; this yields two iterables of elements, either `bs4.element.NavigableString` or `bs4.element.Tag`.
2. Compare each element of the first iterable with each element of the second one. A match is only allowed in two cases:
	- Both elements are `bs4.element.NavigableString`'s (depending on the *cuttable words mode* configuration, matching is done on the raw string, a list of words or on the raw string split in substrings);
	- Both elements are `bs4.element.Tag`'s and their `name` and `attrs` attributes exactly match.
3. Each match is temporarily stored, together with a "score":
	- For `bs4.element.NavigableString` matches, their matching length as per `difflib.SequenceMatcher`;
	- For `bs4.element.Tag` matches that are treated as blocks (those that test `True` with a function of `config.config.tags_fcts_as_blocks`), tags that differ have a matching length of `0`. Tags comparing equal are assigned following matching length: the length of the tag itself for *empty* tags (e.g. `<br />`) (this is a mostly arbitrary choice), else the length of the content of the tag (`tag.string`);
	- For other, "conventional" `bs4.element.Tag` matches, the matching length is the sum of matching lengths of their children using the same algorithm recursively.
4. The highest scoring match is kept and the algorithm recursively repeated on the subiterables before and after the matching elements. Each match thus gets (maximally) a `match_before` and a `match_after` assigned.
5. Regions without match are stored as "no-matches". With them, both iterables are completely covered by matches and no-matches.


#### Dumping

6. With those tree match structures, dumping can be done directly, recursively, by dumping the `match_before` first, then the matched element itself, finally the `match_after`. Matched `bs4.element.NavigableString`'s are dumped parts by parts following the blocks (of words or of characters, depending on the *cuttable words mode* configuration) found by `difflib.SequenceMatcher`. Matched `bs4.element.Tag`'s to be treated as blocks are either dumped without change if fully matching, else are first completely deleted and then completely reinserted. No-matches elements are dumped as completely deleted and completely inserted.
7. Dumping is done in a `BeautifulSoup4` soup, then output as a string.
