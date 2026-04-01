# swb - Static Web Builder

Build and deploy static websites from markdown files. Write your content in markdown, organize pages using your file system, and deploy to Firebase Hosting with a single command.

## Quick Start

```bash
# Create a new site
swb mysite

# Edit your content
cd mysite
vim index.md

# Build the site
swb build .

# Deploy to Firebase
swb deploy .
```

## Installation

### From Source (Development)

```bash
git clone <repo-url>
cd swb
./install.sh
```

### Binary

```bash
./build.sh
# Binary at dist/swb
```

Requires Python 3.12+ and a virtual environment.

## Commands

| Command | Description |
|---------|-------------|
| `swb <name>` | Create a new project |
| `swb build <dir>` | Build the static site |
| `swb deploy <dir>` | Deploy to Firebase Hosting |
| `swb config` | Configure Firebase credentials |
| `swb --version` | Show version |
| `swb --verbose` | Enable debug logging |

## How It Works

### File System Routing

Your directory structure becomes your URL structure:

```
mysite/
  index.md          →  yoursite.com/
  about.md          →  yoursite.com/about
  contact/
    form.md         →  yoursite.com/contact/form
  blog/
    first-post.md   →  yoursite.com/blog/first-post
```

### Project Structure

When you run `swb mysite`, this structure is created:

```
mysite/
  .swb                     # Project marker file
  site.yaml                # Site configuration
  index.md                 # Your homepage
  templates/
    base.html              # HTML wrapper template
  context/
    global.yaml            # Global template variables
  assets/
    css/
      default.css          # Default stylesheet
      custom.css           # Your custom styles
```

### Writing Pages

Pages are markdown files with optional Jinja2 variables:

```markdown
# Welcome to {{ site.title }}

This page was built on {{ build_date }}.

Contact us at [our form](/contact/form).
```

### Template Variables

Variables are injected from three sources (later overrides earlier):

1. **Global context** (`context/global.yaml`) - available on all pages
2. **Per-page context** (`context/<page-name>.yaml`) - available on one page
3. **Site metadata** (`site.yaml` → `{{ site.title }}`, `{{ site.author }}`, etc.)

Built-in variables: `{{ swb_version }}`, `{{ build_date }}`

**Example `context/global.yaml`:**

```yaml
company: Acme Corp
support_email: help@acme.com
```

Then in any markdown file: `Contact {{ company }} at {{ support_email }}`

### Custom HTML Templates

Edit `templates/base.html` to customize the HTML wrapper for all pages:

```html
<!DOCTYPE html>
<html lang="{{ site.language }}">
<head>
    <meta charset="UTF-8">
    <title>{{ page_title }} - {{ site.title }}</title>
    {% for css in css_files %}
    <link rel="stylesheet" href="{{ site_root }}css/{{ css }}">
    {% endfor %}
</head>
<body>
    <nav>
        <a href="{{ site_root }}index.html">Home</a>
        <a href="{{ site_root }}about.html">About</a>
    </nav>
    <main>{{ content }}</main>
    <footer>Built with swb</footer>
</body>
</html>
```

### Custom CSS

Edit `assets/css/custom.css` or add more CSS files to `assets/css/`. All CSS files are automatically discovered and linked.

### Inline HTML

You can use raw HTML directly in your markdown files:

```markdown
# My Page

<div class="hero">
    <h2>Welcome</h2>
    <p>This is custom HTML inside markdown.</p>
</div>

Back to regular markdown here.
```

## Configuration

### Site Config (`site.yaml`)

```yaml
metadata:
  title: "My Site"
  author: "Your Name"
  description: "A great website"
  language: "en-US"

default_css:
  - "default.css"
  - "custom.css"

output:
  dir: "build"
```

### Firebase Setup

1. Install Firebase CLI: `npm install -g firebase-tools`
2. Login: `firebase login`
3. Create a Firebase project at [console.firebase.google.com](https://console.firebase.google.com)
4. Configure swb: `swb config`
5. Build and deploy: `swb build . && swb deploy .`

**Custom domain:** After deploying, add a custom domain in the Firebase Console under Hosting > Add custom domain. Firebase provides free SSL certificates automatically.

## Build Output

`swb build .` generates a `build/` directory:

```
build/
  index.html
  about.html
  contact/
    form.html
  css/
    default.css
    custom.css
```

This is a standard static site that can be served by any web server.

## Markdown Features

swb supports standard markdown plus these extensions:

- **Tables** - GitHub-flavored markdown tables
- **Fenced code blocks** - Triple-backtick code blocks with syntax highlighting
- **Footnotes** - `[^1]` style footnotes
- **Inline HTML** - Raw HTML blocks in markdown

## Dependencies

- Python 3.12+
- `markdown` - Markdown to HTML conversion
- `Jinja2` - Template engine
- `PyYAML` - YAML parsing
- `Pygments` - Syntax highlighting
- `firebase-tools` (npm) - For deployment only

## License

MIT
