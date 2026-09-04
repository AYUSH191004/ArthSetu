import { setReviewerId } from "./api";

const KEY = "arthsetu.reviewer";

export const REVIEWERS = [
  "reviewer_demo",
  "reviewer_krishna",
  "reviewer_asha",
  "reviewer_ravi",
];

export function getReviewer(): string {
  try {
    return localStorage.getItem(KEY) || REVIEWERS[0];
  } catch {
    return REVIEWERS[0];
  }
}

export function setReviewer(id: string) {
  try {
    localStorage.setItem(KEY, id);
  } catch {
    /* storage blocked */
  }
  setReviewerId(id);
}

// apply the persisted identity to the API client at startup
setReviewerId(getReviewer());
