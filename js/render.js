import { filterSources, getSourceById } from "./state.js";

export function renderApp(context) {
  bindSearch(context);
  bindSort(context);
  bindClearFilters(context);
  renderFilters(context);
  renderStatusFilters(context);
  renderMetrics(context);
  renderCollections(context);
  renderSourceSummary(context);
  renderCards(context);
  renderReader(context);
  renderCourse(context);
  renderCandidates(context);
}

function bindSearch({ state, elements, actions }) {
  if (!elements.searchInput) return;

  if (elements.searchInput.value !== state.query) {
    elements.searchInput.value = state.query;
  }

  elements.searchInput.oninput = (event) => {
    actions.onSearchChange(event.target.value);
  };
}

function bindSort({ state, elements, actions }) {
  if (!elements.sortSelect) return;

  if (elements.sortSelect.value !== state.sort) {
    elements.sortSelect.value = state.sort;
  }

  elements.sortSelect.onchange = (event) => {
    actions.onSortChange(event.target.value);
  };
}

function bindClearFilters({ state, elements, actions }) {
  if (!elements.clearFilters) return;

  const filtersAreActive =
    state.category !== "全部" || state.status !== "all" || state.query.trim() !== "" || state.sort !== "priority";

  elements.clearFilters.hidden = !filtersAreActive;
  elements.clearFilters.onclick = () => {
    actions.onClearFilters();
  };
}

function renderFilters({ categories, state, elements, actions }) {
  if (!elements.categoryFilters) return;

  elements.categoryFilters.innerHTML = categories
    .map(
      (category) => `
        <button class="filter-chip ${state.category === category ? "active" : ""}" data-category="${category}">
          ${category}
        </button>
      `,
    )
    .join("");

  elements.categoryFilters.querySelectorAll("[data-category]").forEach((button) => {
    button.addEventListener("click", () => {
      actions.onCategoryChange(button.dataset.category);
    });
  });
}

function renderStatusFilters({ state, elements, actions }) {
  elements.statusFilters.forEach((button) => {
    button.classList.toggle("active", button.dataset.status === state.status);
    button.onclick = () => {
      actions.onStatusChange(button.dataset.status);
    };
  });
}

function renderMetrics({ sources, firstPartyPlatformNames, state, elements }) {
  const official = sources.filter(
    (source) =>
      source.category === "官方文档" ||
      source.platform.includes("官方") ||
      firstPartyPlatformNames.some((platform) => source.platform.includes(platform)),
  ).length;
  const readCount = state.read.size;
  const progress = sources.length ? Math.round((readCount / sources.length) * 100) : 0;

  elements.totalCount.textContent = String(sources.length);
  elements.officialCount.textContent = String(official);
  elements.readCount.textContent = String(readCount);
  elements.progressCount.textContent = `${progress}%`;
}

function renderCollections({ sources, collections, elements, actions }) {
  if (!elements.collectionCards || !collections?.length) return;

  elements.collectionCards.innerHTML = collections
    .map((collection) => {
      const sourceButtons = collection.sourceIds
        .map((id) => {
          const source = getSourceById(sources, id);
          if (!source) return "";
          return `<button data-collection-source="${id}">${source.title}</button>`;
        })
        .join("");

      return `
        <article class="collection-card">
          <div>
            <span class="tag secondary">${collection.sourceIds.length} 份资料</span>
            <h3>${collection.title}</h3>
            <p>${collection.description}</p>
          </div>
          <p class="collection-outcome"><strong>学完能做到：</strong>${collection.outcome}</p>
          <div class="collection-links">
            ${sourceButtons}
          </div>
        </article>
      `;
    })
    .join("");

  elements.collectionCards.querySelectorAll("[data-collection-source]").forEach((button) => {
    button.addEventListener("click", () => {
      actions.onJumpSource(button.dataset.collectionSource);
    });
  });
}

function renderSourceSummary({ sources, categories, state, elements }) {
  const items = filterSources(sources, state);
  if (elements.activeCount) {
    elements.activeCount.textContent = `当前显示 ${items.length} / 总计 ${sources.length}`;
  }

  if (!elements.categorySummary) return;

  const categoryCounts = items.reduce((counts, source) => {
    counts.set(source.category, (counts.get(source.category) || 0) + 1);
    return counts;
  }, new Map());
  const summaryCards = categories
    .filter((category) => category !== "全部")
    .map((category) => ({
      category,
      count: categoryCounts.get(category) || 0,
    }))
    .filter(({ count }) => count > 0);

  elements.categorySummary.innerHTML = summaryCards
    .map(
      ({ category, count }) => `
        <article class="summary-card ${state.category === category ? "active" : ""}">
          <strong>${count}</strong>
          <span>${category}</span>
        </article>
      `,
    )
    .join("");
}

function renderCards({ sources, state, elements, actions }) {
  const items = filterSources(sources, state);

  if (!items.length) {
    elements.sourceCards.innerHTML = `<div class="empty-state">没有找到匹配资料。换个关键词或分类试试。</div>`;
    return;
  }

  const selectedId = state.selectedId && items.some((item) => item.id === state.selectedId) ? state.selectedId : "";

  elements.sourceCards.innerHTML = items
    .map((source) => {
      const isRead = state.read.has(source.id);
      return `
        <article class="source-card ${selectedId === source.id ? "selected" : ""}" data-source-id="${source.id}" tabindex="0">
          <div class="card-meta">
            <span class="tag">${source.category}</span>
            <span class="tag secondary">${source.priority}</span>
            <span class="tag neutral">${source.module}</span>
          </div>
          <h3>${source.title}</h3>
          <p>${source.usefulFor}</p>
          <div class="tag-row">
            ${source.focus.slice(0, 3).map((item) => `<span class="tag neutral">${item}</span>`).join("")}
          </div>
          <div class="card-footer">
            <span class="tag neutral">${source.platform}</span>
            <button class="read-toggle ${isRead ? "done" : ""}" data-read-id="${source.id}">
              ${isRead ? "已读" : "标记已读"}
            </button>
          </div>
        </article>
      `;
    })
    .join("");

  elements.sourceCards.querySelectorAll("[data-source-id]").forEach((card) => {
    card.addEventListener("click", (event) => {
      if (event.target.closest("[data-read-id]")) return;
      actions.onSelectSource(card.dataset.sourceId);
    });
    card.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        actions.onSelectSource(card.dataset.sourceId);
      }
    });
  });

  elements.sourceCards.querySelectorAll("[data-read-id]").forEach((button) => {
    button.addEventListener("click", () => {
      actions.onToggleRead(button.dataset.readId);
    });
  });
}

function renderReader({ sources, state, elements, actions }) {
  const source = state.selectedId ? getSourceById(sources, state.selectedId) : null;

  if (!source) {
    elements.readerDetail.classList.add("collapsed");
    elements.readerDetail.innerHTML = `<div class="empty-state reader-empty">选择资料卡片查看详情。</div>`;
    return;
  }

  elements.readerDetail.classList.remove("collapsed");
  const isRead = state.read.has(source.id);
  elements.readerDetail.innerHTML = `
    <div class="card-meta">
      <span class="tag">${source.category}</span>
      <span class="tag secondary">${source.priority}</span>
      <span class="tag neutral">${isRead ? "已读" : "未读"}</span>
    </div>
    <h3>${source.title}</h3>
    <p><strong>平台：</strong>${source.platform}</p>
    <p><strong>学习用途：</strong>${source.module}</p>
    <p><strong>为什么读：</strong>${source.usefulFor}</p>
    <p><strong>阅读笔记：</strong>${source.note}</p>
    <p><strong>重点看：</strong></p>
    <ul>
      ${source.focus.map((item) => `<li>${item}</li>`).join("")}
    </ul>
    <button class="read-toggle ${isRead ? "done" : ""}" data-detail-read="${source.id}">
      ${isRead ? "取消已读" : "标记为已读"}
    </button>
    <a class="source-link" href="${source.url}" target="_blank" rel="noreferrer">打开原文链接</a>
  `;

  elements.readerDetail.querySelector("[data-detail-read]").addEventListener("click", () => {
    actions.onToggleRead(source.id);
  });
}

function renderCourse({ sources, learningPaths, elements, actions }) {
  elements.courseTimeline.innerHTML = learningPaths
    .map(
      (item) => `
        <article class="timeline-item">
          <div class="timeline-time">${item.time}</div>
          <div>
            <h3>${item.title}</h3>
            <p>${item.body}</p>
            <div class="timeline-links">
              ${item.sourceIds
                .map((id) => {
                  const source = getSourceById(sources, id);
                  if (!source) return "";
                  return `<button data-jump-source="${id}">${source.title}</button>`;
                })
                .join("")}
            </div>
          </div>
        </article>
      `,
    )
    .join("");

  elements.courseTimeline.querySelectorAll("[data-jump-source]").forEach((button) => {
    button.addEventListener("click", () => {
      actions.onJumpSource(button.dataset.jumpSource);
    });
  });
}

function renderCandidates({ candidates, sources, elements, actions }) {
  if (!elements.candidateList) return;

  elements.candidateList.innerHTML = candidates
    .map((candidate) => {
      const source = getSourceById(sources, candidate.sourceId);
      if (!source) return "";

      return `
        <li>
          <div class="candidate-copy">
            <span class="tag secondary">${candidate.track}</span>
            <strong>${source.title}</strong>
            <p>${candidate.description}</p>
          </div>
          <div class="candidate-actions">
            <button type="button" data-candidate-source="${source.id}">查看阅读笔记</button>
            <a class="candidate-link" data-candidate-link href="${source.url}" target="_blank" rel="noreferrer">打开原文</a>
          </div>
        </li>
      `;
    })
    .join("");

  elements.candidateList.querySelectorAll("[data-candidate-source]").forEach((button) => {
    button.addEventListener("click", () => {
      actions.onJumpSource(button.dataset.candidateSource);
    });
  });
}
