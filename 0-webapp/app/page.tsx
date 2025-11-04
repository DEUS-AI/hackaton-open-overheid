import { redirect } from "next/navigation";

// Lightweight root page: redirect to the canonical /home route.
export default function RootIndex() {
  redirect("/home");
}
