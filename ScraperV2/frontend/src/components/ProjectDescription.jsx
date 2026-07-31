import React from 'react';

export default function ProjectDescription() {
	return (
    <div className="flex h-full flex-col text-start text-on-surface-variant">
      <div className="space-y-4">
        <p>
          This project aims to build a practical system for retrieving and extracting
          selected information from open-access research papers available online. Its
          purpose is to support evidence synthesis, literature review, and related
          research workflows by automatically identifying high-value content from
          full-text scientific articles.
        </p>
        <br />
        <p>
          The main focus is on extracting <strong>Risk of bias</strong> information
          and <strong>Methods</strong> sections from papers hosted in repositories such as
          PubMed Central, arXiv, and medRxiv. The system is intended to accept one DOI
          or a collection of DOIs, retrieve the corresponding articles, parse them into
          a structured machine-readable form, and detect the most relevant fragments of
          content for further analysis.
        </p>
        <br />
        <p>
          A key part of the project is handling the fact that important information may
          appear in different forms, including standard text sections, tables, and other
          structured elements. For that reason, the solution combines document
          structure, pattern matching, and rule-based extraction approaches, with the
          option to extend the pipeline using NLP methods where useful.
        </p>
        <br />
        <p>
          The final goal is a browser-based application that allows the user to submit
          paper identifiers and receive structured, comparable results that can later be
          exported for downstream use, for example in evidence synthesis or literature
          review workflows.
        </p>
      </div>

      <div className="mt-auto flex justify-end pt-8">
        <a
          href="#data-extraction"
          className="inline-flex items-center rounded bg-primary px-5 py-3 text-sm font-semibold text-primary-foreground transition-transform duration-200 hover:-translate-y-0.5 hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 focus:ring-offset-surface_container"
        >
          Get Started
        </a>
      </div>
    </div>
	);
}
