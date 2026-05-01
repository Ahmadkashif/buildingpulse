import { leadHandlers } from "./handlers/lead";
import { predictionHandlers } from "./handlers/prediction";
import { scenarioHandlers } from "./handlers/scenario";
import { sponsorHandlers } from "./handlers/sponsor";

export const handlers = [
  ...predictionHandlers,
  ...sponsorHandlers,
  ...leadHandlers,
  ...scenarioHandlers,
];
