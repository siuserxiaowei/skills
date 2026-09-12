export function createInitialState(sources) {
  return {
    category: "全部",
    status: "all",
    query: "",
    sort: "priority",
    selectedId: sources[0]?.id || "",
    read: new Set(
      JSON.parse(
        localStorage.getItem("agentArchitectureReadSources") ||
          localStorage.getItem("hrAgentReadSources") ||
          "[]",
      ),
    ),
  };
}

export function saveReadState(state) {
  localStorage.setItem("agentArchitectureReadSources", JSON.stringify([...state.read]));
}

export function getSourceById(sources, id) {
  return sources.find((source) => source.id === id);
}

const priorityOrder = new Map(
  ["先读", "案例", "参考", "补基础", "扩展"].map((priority, index) => [priority, index]),
);

function compareText(left, right) {
  return left.localeCompare(right, "zh-CN", { sensitivity: "base" });
}

function compareSources(left, right, sort) {
  if (sort === "category") {
    return compareText(left.source.category, right.source.category) || left.index - right.index;
  }

  if (sort === "platform") {
    return compareText(left.source.platform, right.source.platform) || left.index - right.index;
  }

  const leftPriority = priorityOrder.get(left.source.priority) ?? priorityOrder.size;
  const rightPriority = priorityOrder.get(right.source.priority) ?? priorityOrder.size;
  return leftPriority - rightPriority || left.index - right.index;
}

export function filterSources(sources, state) {
  const query = state.query.trim().toLowerCase();
  return sources
    .map((source, index) => ({ source, index }))
    .filter(({ source }) => {
      const inCategory = state.category === "全部" || source.category === state.category;
      const isRead = state.read.has(source.id);
      const inStatus = state.status === "all" || (state.status === "read" ? isRead : !isRead);
      const haystack = [
        source.title,
        source.platform,
        source.category,
        source.module,
        source.usefulFor,
        source.note,
        ...source.focus,
      ]
        .join(" ")
        .toLowerCase();
      return inCategory && inStatus && (!query || haystack.includes(query));
    })
    .sort((left, right) => compareSources(left, right, state.sort))
    .map(({ source }) => source);
}
