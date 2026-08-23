document.addEventListener("DOMContentLoaded", () => {
  const sections = Array.from(
    document.querySelectorAll(".cv-section, .publications-section")
  );
  const toc = document.querySelector("body > #TOC");
  const headerActions = document.querySelector(".cv-name-actions");
  const expandButton = document.querySelector(".js-expand-all");
  const collapseButton = document.querySelector(".js-collapse-all");
  const printButton = document.querySelector(".js-print");

  if (toc) {
    document.body.classList.add("has-cv-toc");
  }

  if (toc && headerActions) {
    headerActions.classList.add("cv-toc-controls");
    toc.appendChild(headerActions);
  }

  if (toc && !toc.querySelector(".cv-toc-toggle")) {
    const title = toc.querySelector("h2");
    const toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "cv-toc-toggle";
    toggle.textContent = title?.textContent?.trim() || "Table of contents";
    toggle.setAttribute("aria-expanded", "false");
    toc.insertBefore(toggle, toc.firstChild);

    toggle.addEventListener("click", () => {
      const open = toc.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", String(open));
    });

    toc.querySelectorAll('a[href^="#"]').forEach((link) => {
      link.addEventListener("click", () => {
        if (window.matchMedia("(max-width: 1359px)").matches) {
          toc.classList.remove("is-open");
          toggle.setAttribute("aria-expanded", "false");
        }
      });
    });
  }

  [
    [expandButton, "Expand all sections"],
    [collapseButton, "Collapse all sections"],
    [printButton, "Print to PDF"],
  ].forEach(([button, label]) => {
    if (!button) return;
    button.setAttribute("aria-label", label);
    button.setAttribute("title", label);
  });

  const enhanceEntries = (root) => {
    const lists = root.querySelectorAll("ul, ol");
    lists.forEach((list) => {
      let enhancedCount = 0;
      Array.from(list.children).forEach((item) => {
        if (item.tagName !== "LI") return;
        const raw = item.innerHTML;
        const splitAt = raw.indexOf(" | ");
        if (splitAt === -1) return;

        const dateHTML = raw.slice(0, splitAt).trim();
        const bodyHTML = raw.slice(splitAt + 3).trim();
        if (!dateHTML || !bodyHTML) return;

        item.innerHTML = `
          <span class="cv-entry__date">${dateHTML}</span>
          <span class="cv-entry__marker" aria-hidden="true">◇</span>
          <div class="cv-entry__body">${bodyHTML}</div>
        `;
        item.classList.add("cv-entry");
        enhancedCount += 1;
      });

      if (enhancedCount > 0) {
        list.classList.add("cv-entry-list");
      }
    });
  };

  const enhancedSections = sections
    .map((section) => {
      const heading = section.querySelector(":scope > h2");
      if (!heading) return null;

      const content = document.createElement("div");
      content.className = "section-content";

      let sibling = heading.nextElementSibling;
      while (sibling) {
        const next = sibling.nextElementSibling;
        content.appendChild(sibling);
        sibling = next;
      }

      const button = document.createElement("button");
      button.type = "button";
      button.className = "cv-section__toggle";
      button.textContent = heading.textContent.trim();
      button.setAttribute("aria-expanded", "true");

      if (heading.id) {
        content.id = `${heading.id}-panel`;
        button.setAttribute("aria-controls", content.id);
      }

      heading.remove();
      section.prepend(button);
      section.appendChild(content);
      section.classList.add("is-enhanced");
      enhanceEntries(content);

      button.addEventListener("click", () => {
        const expanded = button.getAttribute("aria-expanded") === "true";
        button.setAttribute("aria-expanded", String(!expanded));
        section.classList.toggle("is-collapsed", expanded);
        syncControls();
      });

      return { section, button };
    })
    .filter(Boolean);

  function setAllSections(expanded) {
    enhancedSections.forEach(({ section, button }) => {
      button.setAttribute("aria-expanded", String(expanded));
      section.classList.toggle("is-collapsed", !expanded);
    });
    syncControls();
  }

  function syncControls() {
    // Controls remain clickable even when the requested state is already true.
  }

  if (expandButton) {
    expandButton.addEventListener("click", (event) => {
      event.preventDefault();
      setAllSections(true);
    });
  }

  if (collapseButton) {
    collapseButton.addEventListener("click", (event) => {
      event.preventDefault();
      setAllSections(false);
    });
  }

  if (printButton) {
    printButton.addEventListener("click", (event) => {
      event.preventDefault();
      setAllSections(true);
      window.print();
    });
  }

  window.addEventListener("beforeprint", () => {
    setAllSections(true);
  });

  syncControls();
});
