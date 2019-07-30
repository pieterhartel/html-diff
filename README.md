# HTML-Diff: HTML-formatted diff'ing of HTML snippets

Compares two HTML snippets strings and returns the diff as a valid HTML snippet with changes wrapped in &lt;del&gt; and &lt;ins&gt; tags.

Relies on ```BeautifulSoup4``` with ```html.parser``` backend for HTML parsing and dumping.


## Usage

```python
>>> from html_diff import diff
>>> diff("<em>ABC</em>", "<em>AB</em>C")
'<em>AB<del>C</del></em><ins>C</ins>'
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
- ```-b``` or ```--blocks```: definitions of functions to be added to ```tags_fcts_as_blocks```, e.g. for treating ```<span class="math-tex">\(...\)</span>``` as insecable blocks:

```bash
python -m html_diff -b 'lambda tag: tag.name == "span" and "math-tex" in tag.attrs.get("class", [])'
```

