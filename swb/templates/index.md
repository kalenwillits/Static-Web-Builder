# Welcome to {{ site.title }}

This is your homepage. Edit this file to add your own content.

## Getting Started

1. Edit `site.yaml` to set your site's metadata
2. Add markdown files anywhere in the project to create new pages
3. The file system structure becomes your site's URL structure
4. Run `swb build .` to build your site

## File System Routing

Pages are routed based on their location in the project:

- `index.md` → `/`
- `about.md` → `/about`
- `contact/form.md` → `/contact/form`

## Using Variables

You can use Jinja2 variables in your markdown files:

- Site title: {{ site.title }}
- Author: {{ site.author }}
- Build date: {{ build_date }}

Add your own variables in `context/global.yaml`.
