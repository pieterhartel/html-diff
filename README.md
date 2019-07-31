# HTML-Diff: HTML-formatted diff'ing of HTML snippets

Compares two HTML snippets strings and returns the diff as a valid HTML snippet with changes wrapped in `<del>` and `<ins>` tags.

Relies on `BeautifulSoup4` with `html.parser` backend for HTML parsing and dumping.

HTML-Diff focusses on providing *valid* diffs, that is:

1. The returned strings represent valid HTML snippets;
2. Provided that the input snippets represent valid HTML snippets containing no `<del>` or `<ins>` tags, they can be identically reconstructed from the diff output, by removing `<ins>` tags and their content and replacing `<del>` tags by their content for the *old* snippet, the other way round for the *new* one. Functions are provided in the `check` module for those reconstructions and checking that the reconstructions match the inputs.


## Usage

### Basic usage

```python
>>> from html_diff import diff
>>> diff("<em>ABC</em>", "<em>AB</em>C")
'<em>AB<del>C</del></em><ins>C</ins>'
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
>>> diff(r'<span class="math-tex">\(\vec{v}\)</span>', r'<span class="math-tex">\(\vec{w}\)</span>')
'<del><span class="math-tex">\\(\\vec{v}\\)</span></del><ins><span class="math-tex">\\(\\vec{w}\\)</span></ins>'
```

The functions in `config.config.tags_fcts_as_blocks` should take a `bs4.element.Tag` as input and return a `bool`; the tags are tested against all functions in the list, and are considered insecable blocks if any call returns `True`.


### Preventing word cut in diff

By default, the diff'ing algorithm for plain text parts does not care about words - if a word part is modified, that part gets `<del>`'ed and `<ins>`'ed, while the rest of the word remains untouched. It may however be more readable to have full words deleted and reinserted. To ensure this, switch `config.config.cuttable_words` to `False`:


`config.config.cuttable_words == True` (default):

```python
>>> diff("OlyExams", "ExamTools")
'<del>Oly</del>Exam<ins>Tool</ins>s'
```

`config.config.cuttable_words == False`:

```python
>>> diff("OlyExams", "ExamTools")
'<del>OlyExams</del><ins>ExamTools</ins>'
```

In uncuttable words mode, non-word characters correspond to `re`'s `\W` pattern.


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

at the root of the project and navigate to 127.0.0.1:8080 with your browser.

You can specify further options:

- `-a` or `--address`: custom address of the server (default: 127.0.0.1)
- `-p` or `--port`: custom port of the server (default: 8080)
- `-b` or `--blocks`: definitions of functions to be added to `config.config.tags_fcts_as_blocks`, e.g.:

```bash
python -m html_diff -b 'lambda tag: tag.name == "span" and "math-tex" in tag.attrs.get("class", [])'
```

- `-u` or `--uncuttable-words`: prevent cutting words in the diff (modified words are entirely deleted and reinserted)

