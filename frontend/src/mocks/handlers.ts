import { buildingHandlers } from "./handlers/building";
import { forecastHandlers } from "./handlers/forecast";
import { reportHandlers } from "./handlers/report";

export const handlers = [...buildingHandlers, ...forecastHandlers, ...reportHandlers];
