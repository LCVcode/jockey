# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information


import os
import sys


sys.path.insert(0, os.path.abspath("../src"))

github_username = "LCVcode"
github_repository = "jockey"
author = "Connor Chamberlain"
project = "Juju Jockey"
copyright = "2024 Connor Chamberlain"
language = "en"
package_root = "src/jockey"
extensions = [
    "sphinx.ext.doctest",
    "sphinx.ext.intersphinx",
    "sphinx.ext.mathjax",
    "sphinx.ext.todo",
    "autoapi.extension",
    "myst_parser",
    "canonical_sphinx",
]
templates_path = [
    "_templates",
]
html_static_path = [
    "_static",
]
source_suffix = [".rst", ".md"]
master_doc = "index"
html_theme = "canonical_sphinx"
add_module_names = True
hide_none_rtype = True
all_typevars = True
autosummary_generate = True
overloads_location = "bottom"
autoclass_content = "both"
set_type_checking_flag = True
autoapi_dirs = ["../src"]
autoapi_type = "python"
autoapi_typehints = "both"
autoapi_options = [
    "members",
    "undoc-members",
    "show-inheritance",
    "show-module-summary",
    "imported-members",
]

html_context = {
    # Change to the link to the website of your product (without "https://")
    # For example: "ubuntu.com/lxd" or "microcloud.is"
    # If there is no product website, edit the header template to remove the
    # link (see the readme for instructions).
    "product_page": "github.com/LCVcode/jockey",
    # Add your product tag (the orange part of your logo, will be used in the
    # header) to ".sphinx/_static" and change the path here (start with "_static")
    # (default is the circle of friends)
    # "product_tag": "",
    # Change to the discourse instance you want to be able to link to
    # using the :discourse: metadata at the top of a file
    # (use an empty value if you don't want to link)
    "discourse": "",
    # Change to the GitHub URL for your project
    "github_url": "https://github.com/LCVcode/jockey",
    # Change to the branch for this version of the documentation
    "github_version": "master",
    # Change to the folder that contains the documentation
    # (usually "/" or "/docs/")
    "github_folder": "/docs/",
    # Change to an empty value if your GitHub repo doesn't have issues enabled.
    # This will disable the feedback button and the issue link in the footer.
    "github_issues": "enabled",
    # Controls the existence of Previous / Next buttons at the bottom of pages
    # Valid options: none, prev, next, both
    "sequential_nav": "none",
    # Controls whether to display the contributors for each file
    "display_contributors": True,
}

html_theme_options = {
    "light_css_variables": {
        "color-sidebar-background-border": "none",
        "font-stack": (
            "Ubuntu, -apple-system, Segoe UI, Roboto, Oxygen, Cantarell, "
            "Fira Sans, Droid Sans, Helvetica Neue, sans-serif"
        ),
        "font-stack--monospace": "Ubuntu Mono, Consolas, Monaco, Courier, monospace",
        "color-foreground-primary": "#111",
        "color-foreground-secondary": "var(--color-foreground-primary)",
        "color-foreground-muted": "#333",
        "color-background-secondary": "#FFF",
        "color-background-hover": "#f2f2f2",
        "color-brand-primary": "#111",
        "color-brand-content": "#06C",
        "color-api-background": "#cdcdcd",
        "color-inline-code-background": "rgba(0,0,0,.03)",
        "color-sidebar-link-text": "#111",
        "color-sidebar-item-background--current": "#ebebeb",
        "color-sidebar-item-background--hover": "#f2f2f2",
        "toc-font-size": "var(--font-size--small)",
        "color-admonition-title-background--note": "var(--color-background-primary)",
        "color-admonition-title-background--tip": "var(--color-background-primary)",
        "color-admonition-title-background--important": "var(--color-background-primary)",
        "color-admonition-title-background--caution": "var(--color-background-primary)",
        "color-admonition-title--note": "#24598F",
        "color-admonition-title--tip": "#24598F",
        "color-admonition-title--important": "#C7162B",
        "color-admonition-title--caution": "#F99B11",
        "color-highlighted-background": "#EbEbEb",
        "color-link-underline": "var(--color-background-primary)",
        "color-link-underline--hover": "var(--color-background-primary)",
        "color-version-popup": "#772953",
    },
    "dark_css_variables": {
        "color-foreground-secondary": "var(--color-foreground-primary)",
        "color-foreground-muted": "#CDCDCD",
        "color-background-secondary": "var(--color-background-primary)",
        "color-background-hover": "#666",
        "color-brand-primary": "#fff",
        "color-brand-content": "#06C",
        "color-sidebar-link-text": "#f7f7f7",
        "color-sidebar-item-background--current": "#666",
        "color-sidebar-item-background--hover": "#333",
        "color-admonition-background": "transparent",
        "color-admonition-title-background--note": "var(--color-background-primary)",
        "color-admonition-title-background--tip": "var(--color-background-primary)",
        "color-admonition-title-background--important": "var(--color-background-primary)",
        "color-admonition-title-background--caution": "var(--color-background-primary)",
        "color-admonition-title--note": "#24598F",
        "color-admonition-title--tip": "#24598F",
        "color-admonition-title--important": "#C7162B",
        "color-admonition-title--caution": "#F99B11",
        "color-highlighted-background": "#666",
        "color-link-underline": "var(--color-background-primary)",
        "color-link-underline--hover": "var(--color-background-primary)",
        "color-version-popup": "#F29879",
    },
}

intersphinx_mapping = {
    "python": ("https://docs.python.org/{.major}".format(sys.version_info), None),
    "dotty_dict": ("https://dotty-dict.readthedocs.io/en/latest/", None),
}
