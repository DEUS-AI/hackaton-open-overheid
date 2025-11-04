// Legacy route placeholder: previously document-status; redirecting to processed-documents.
import { redirect } from "next/navigation";

export default function DocumentStatusLegacy() {
	redirect("/processed-documents");
}
