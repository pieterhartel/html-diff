# HTML-Diff: HTML-formatted diff'ing of HTML snippets

Compares two HTML snippets strings and returns the diff as a valid HTML snippet with changes wrapped in ```<del>``` and ```<ins>``` tags.

Relies on ```BeautifulSoup4``` with ```html.parser``` backend for HTML parsing and dumping.


## Usage

### Basic usage

```python
>>> from html_diff import diff
>>> diff("<em>ABC</em>", "<em>AB</em>C")
'<em>AB<del>C</del></em><ins>C</ins>'
```


### Add custom tags to be treated as insecable blocks

Example use case: having MathJax elements wrapped into ```<span class="math-tex">\(...\)</span>``` and wanting to avoid ```<del>``` and ```<ins>``` tags inside the ```\(...\)``` (which would be badly rendered):

```python
>>> from html_diff import tags_fcts_as_blocks
>>> tags_fcts_as_blocks.append(lambda tag: tag.name == "span" and "math-tex" in tag.attrs.get("class", []))
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

- ```-a``` or ```--address```: custom address of the server (default: 127.0.0.1)
- ```-p``` or ```--port```: custom port of the server (default: 8080)
- ```-b``` or ```--blocks```: definitions of functions to be added to ```tags_fcts_as_blocks```, e.g.:

```bash
python -m html_diff -b 'lambda tag: tag.name == "span" and "math-tex" in tag.attrs.get("class", [])'
```

