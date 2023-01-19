import prodigy
import spacy
import srsly
from prodigy import set_hashes
from prodigy.components.loaders import JSONL


@prodigy.recipe(
    "textcat_topic",
    dataset=("Dataset to save answers to", "positional", None, str),
    examples=("Examples to load from disk", "positional", None, str),
    model=("spaCy model to load", "positional", None, str),
    patterns=("Patterns to match from json file", "positional", None, str),
    tags=(
        "Comma-separated list of tags to filter items from the dataset",
        "positional",
        None,
        lambda d: d.split(","),
    ),
    label=("Label for annotated data", "positional", None, str),
)
def textcat_topic(dataset, examples, model, patterns, tags, label):
    # import spaCy and initialize matcher
    nlp = spacy.load(model)

    # set up stream and set hashes just on text key
    stream = (
        item for item in JSONL(examples) if any(tag in tags for tag in item["tags"])
    )
    stream = (set_hashes(ex, input_keys=("title")) for ex in stream)

    # add matcher pattern to underline
    patterns = srsly.read_jsonl(patterns)
    ruler = nlp.add_pipe("span_ruler")
    ruler.add_patterns(patterns)

    # Render title and description in HTML format for Prodigy as a generator object
    def add_html(examples):
        for ex in examples:
            doc = nlp(ex["description"])

            summary_highlight = ex["description"]
            for span in doc.spans["ruler"]:
                summary_highlight = summary_highlight.replace(
                    span.text, f"<b style='background-color: yellow;'>{span.text}</b>"
                )

            ex[
                "html"
            ] = f"<h3>{ex['title']}</h3><p><font size='3'>{summary_highlight}</font></p><a href='{ex['link']}'>LINK</a>"
            yield ex

    # delete html key in output data and add label key
    def before_db(examples):
        for ex in examples:
            ex["label"] = label
            ex["text"] = ex["title"] + "\n" + ex["description"]
            del ex["html"]
            del ex["title"]
            del ex["description"]
        return examples

    return {
        "before_db": before_db,
        "dataset": dataset,
        "stream": add_html(stream),
        "view_id": "html",
    }
