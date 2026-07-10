import { learningPaths } from "../data/learning-paths.js";
import { collections } from "../data/collections.js";
import { sources } from "../data/sources.js";
import { candidates, categories, firstPartyPlatformNames } from "../data/taxonomy.js";
import { createInitialState, filterSources, getSourceById, saveReadState } from "./state.js";
import { renderApp } from "./render.js";

const state = createInitialState(sources);
const narrowScreenQuery = window.matchMedia("(max-width: 1180px)");

const elements = {
  categoryFilters: document.querySelector("#categoryFilters"),
  sourceCards: document.querySelector("#sourceCards"),
  readerDetail: document.querySelector("#readerDetail"),
  searchInput: document.querySelector("#searchInput"),
  sortSelect: document.querySelector("#sortSelect"),
  activeCount: document.querySelector("#activeCount"),
  categorySummary: document.querySelector("#categorySummary"),
  courseTimeline: document.querySelector("#courseTimeline"),
  candidateList: document.querySelector("#candidateList"),
  statusFilters: document.querySelectorAll("[data-status]"),
  totalCount: document.querySelector("#totalCount"),
  officialCount: document.querySelector("#officialCount"),
  readCount: document.querySelector("#readCount"),
  progressCount: document.querySelector("#progressCount"),
  collectionCards: document.querySelector("#collectionCards"),
  sourcesSection: document.querySelector("#sources"),
  clearFilters: document.querySelector("[data-clear-filters]"),
};

const actions = {
  onCategoryChange(category) {
    state.category = category;
    render();
  },
  onStatusChange(status) {
    state.status = status;
    render();
  },
  onSearchChange(query) {
    state.query = query;
    render();
  },
  onSortChange(sort) {
    state.sort = sort;
    render();
  },
  onClearFilters() {
    state.category = "全部";
    state.status = "all";
    state.query = "";
    state.sort = "priority";
    render();
  },
  onSelectSource(id) {
    state.selectedId = id;
    render();
  },
  onToggleRead(id) {
    if (state.read.has(id)) {
      state.read.delete(id);
    } else {
      state.read.add(id);
    }
    saveReadState(state);
    render();
  },
  onJumpSource(id) {
    state.selectedId = id;
    state.category = "全部";
    state.status = "all";
    state.query = "";
    render();
    elements.sourcesSection.scrollIntoView({ behavior: "smooth" });
  },
  onClearDetailFocus() {
    if (!narrowScreenQuery.matches) return;

    state.selectedId = "";
    if (document.activeElement instanceof HTMLElement) {
      document.activeElement.blur();
    }
    render();
  },
};

function ensureSelectedSourceIsVisible() {
  const items = filterSources(sources, state);
  if (!items.length) return;
  if (narrowScreenQuery.matches && !state.selectedId) return;

  if (items.length && !items.some((item) => item.id === state.selectedId)) {
    state.selectedId = items[0].id;
  }
  if (!getSourceById(sources, state.selectedId)) {
    state.selectedId = sources[0]?.id || "";
  }
}

function render() {
  ensureSelectedSourceIsVisible();
  renderApp({
    sources,
    categories,
    candidates,
    learningPaths,
    collections,
    firstPartyPlatformNames,
    state,
    elements,
    actions,
  });
}

function bindViewportShortcuts() {
  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape" || !narrowScreenQuery.matches) return;
    if (document.activeElement instanceof HTMLElement) {
      const tagName = document.activeElement.tagName;
      if (tagName === "INPUT" || tagName === "TEXTAREA" || tagName === "SELECT") return;
    }
    if (!state.selectedId) return;

    event.preventDefault();
    actions.onClearDetailFocus();
  });

  if (typeof narrowScreenQuery.addEventListener === "function") {
    narrowScreenQuery.addEventListener("change", render);
  } else {
    narrowScreenQuery.addListener(render);
  }
}

bindViewportShortcuts();
render();
