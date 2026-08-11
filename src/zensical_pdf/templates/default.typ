// zensical-pdf default Typst template
// Place this file at the path specified in [paths].template in your zensical-pdf.toml.
// Pandoc passes this template to --template when converting Markdown to Typst.
// Variables available: $title$, $author$, $date$, $version$, $body$

#set document(
  title: "$title$",
  author: "$author$",
)

#set text(
  font: "New Computer Modern",
  size: 11pt,
)

#set page(
  numbering: "1",
  number-align: center,
  margin: (x: 2.5cm, y: 3cm),
)

#set heading(numbering: "1.1.")

#show heading.where(level: 1): it => {
  pagebreak(weak: true)
  block(below: 1em, it)
}

// Title page
#align(center)[
  #v(4cm)
  #text(size: 28pt, weight: "bold")[$title$]
  #v(0.5cm)
  #if "$subtitle$" != "" [
    #text(size: 16pt, style: "italic")[$subtitle$]
    #v(0.5cm)
  ]
  #v(1cm)
  #text(size: 12pt)[$author$]
  #v(0.3cm)
  #if "$version$" != "" [
    #text(size: 10pt, fill: gray)[Version $version$]
    #v(0.3cm)
  ]
  #text(size: 10pt, fill: gray)[$date$]
]

#pagebreak()

// Table of contents
#outline(depth: 3, indent: true)

#pagebreak()

// Document body
$body$
