import { render, screen } from "@testing-library/react";
import { vi } from "vitest";
import SearchBox from "./search-box";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

test("renders search input", () => {
  render(<SearchBox />);
  expect(screen.getByPlaceholderText(/search/i)).toBeInTheDocument();
});
