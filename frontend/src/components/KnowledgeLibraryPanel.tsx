import { ChangeEvent, useMemo, useRef, useState } from "react";

import { KnowledgeDocumentMetadata, KnowledgeUploadInput } from "@/components/studio-types";

type KnowledgeLibraryPanelProps = {
  records: KnowledgeDocumentMetadata[];
  onUpload: (input: KnowledgeUploadInput) => void;
  onRemove: (documentId: string) => void;
};

const ALLOWED_EXTENSIONS = ["pdf", "docx", "txt", "md", "json", "csv"];
const ACCEPT_ATTRIBUTE = ".pdf,.docx,.txt,.md,.json,.csv,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain,text/markdown,application/json,text/csv";

function formatBytes(size: number): string {
  if (size < 1024) {
    return `${size} B`;
  }

  if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(1)} KB`;
  }

  return `${(size / (1024 * 1024)).toFixed(2)} MB`;
}

function isAllowedFile(file: File): boolean {
  const extension = file.name.split(".").pop()?.toLowerCase() ?? "";
  return ALLOWED_EXTENSIONS.includes(extension);
}

function buildUploadInput(file: File, description: string): KnowledgeUploadInput {
  return {
    file,
    metadata: {
      id: crypto.randomUUID(),
      name: file.name,
      size: file.size,
      type: file.type || "application/octet-stream",
      uploadedDate: new Date().toISOString(),
      description,
    },
  };
}

export function KnowledgeLibraryPanel({ records, onUpload, onRemove }: KnowledgeLibraryPanelProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [descriptionDraft, setDescriptionDraft] = useState("");
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const filteredRecords = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();
    if (!query) {
      return records;
    }

    return records.filter((record) => {
      return (
        record.name.toLowerCase().includes(query) ||
        record.type.toLowerCase().includes(query) ||
        record.description.toLowerCase().includes(query)
      );
    });
  }, [records, searchQuery]);

  const stats = useMemo(() => {
    const totalFiles = records.length;
    const totalBytes = records.reduce((sum, record) => sum + record.size, 0);
    const types = new Set(records.map((record) => record.type));
    return {
      totalFiles,
      totalBytes,
      typeCount: types.size,
    };
  }, [records]);

  const handleFileSelection = (event: ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files ?? []);
    if (files.length === 0) {
      return;
    }

    const invalidFile = files.find((file) => !isAllowedFile(file));
    if (invalidFile) {
      setUploadError(`Unsupported file: ${invalidFile.name}. Allowed: ${ALLOWED_EXTENSIONS.join(", ")}.`);
      event.target.value = "";
      return;
    }

    setUploadError(null);

    for (const file of files) {
      onUpload(buildUploadInput(file, descriptionDraft.trim()));
    }

    setDescriptionDraft("");
    event.target.value = "";
  };

  return (
    <section className="space-y-4 rounded-xl border border-zinc-800 bg-zinc-950/70 p-4">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-zinc-100">Knowledge Library</h3>
          <p className="text-xs text-zinc-400">Project-scoped context files for future RAG workflows.</p>
        </div>
        <button
          className="rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-1.5 text-xs font-semibold text-zinc-200 transition hover:border-zinc-600 hover:bg-zinc-800"
          onClick={() => fileInputRef.current?.click()}
          type="button"
        >
          Upload Documents
        </button>
      </header>

      <input
        accept={ACCEPT_ATTRIBUTE}
        className="hidden"
        multiple
        onChange={handleFileSelection}
        ref={fileInputRef}
        type="file"
      />

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <article className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-3">
          <p className="text-xs uppercase tracking-wide text-zinc-500">Uploaded Files</p>
          <p className="mt-2 text-xl font-semibold text-zinc-100">{stats.totalFiles}</p>
        </article>
        <article className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-3">
          <p className="text-xs uppercase tracking-wide text-zinc-500">Storage Size</p>
          <p className="mt-2 text-xl font-semibold text-zinc-100">{formatBytes(stats.totalBytes)}</p>
        </article>
        <article className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-3">
          <p className="text-xs uppercase tracking-wide text-zinc-500">File Types</p>
          <p className="mt-2 text-xl font-semibold text-zinc-100">{stats.typeCount}</p>
        </article>
        <article className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-3">
          <p className="text-xs uppercase tracking-wide text-zinc-500">Supported</p>
          <p className="mt-2 text-sm font-semibold text-zinc-200">PDF DOCX TXT MD JSON CSV</p>
        </article>
      </div>

      <div className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_260px]">
        <label className="text-xs text-zinc-400">
          Search
          <input
            className="mt-1 w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100"
            onChange={(event) => setSearchQuery(event.target.value)}
            placeholder="Search files, types, or descriptions..."
            value={searchQuery}
          />
        </label>
        <label className="text-xs text-zinc-400">
          Description For New Upload
          <input
            className="mt-1 w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100"
            onChange={(event) => setDescriptionDraft(event.target.value)}
            placeholder="Optional document context"
            value={descriptionDraft}
          />
        </label>
      </div>

      {uploadError && (
        <div className="rounded-lg border border-red-500/40 bg-red-500/10 px-3 py-2 text-xs text-red-200">{uploadError}</div>
      )}

      <section className="space-y-2">
        <h4 className="text-xs font-semibold uppercase tracking-wide text-zinc-400">Uploaded Files</h4>
        <div className="overflow-hidden rounded-lg border border-zinc-800">
          <table className="w-full border-collapse text-left text-sm">
            <thead className="bg-zinc-900/90 text-xs uppercase tracking-wide text-zinc-500">
              <tr>
                <th className="px-3 py-2 font-medium">Name</th>
                <th className="px-3 py-2 font-medium">Type</th>
                <th className="px-3 py-2 font-medium">Size</th>
                <th className="px-3 py-2 font-medium">Uploaded</th>
                <th className="px-3 py-2 font-medium">Description</th>
                <th className="px-3 py-2 font-medium">Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredRecords.length === 0 ? (
                <tr>
                  <td className="px-3 py-4 text-sm text-zinc-500" colSpan={6}>
                    No documents found for this project.
                  </td>
                </tr>
              ) : (
                filteredRecords.map((record) => (
                  <tr className="border-t border-zinc-800/70" key={record.id}>
                    <td className="px-3 py-2 text-zinc-200">{record.name}</td>
                    <td className="px-3 py-2 text-zinc-400">{record.type}</td>
                    <td className="px-3 py-2 text-zinc-400">{formatBytes(record.size)}</td>
                    <td className="px-3 py-2 text-zinc-400">{new Date(record.uploadedDate).toLocaleString()}</td>
                    <td className="px-3 py-2 text-zinc-400">{record.description || "-"}</td>
                    <td className="px-3 py-2">
                      <button
                        className="rounded-md border border-zinc-700 px-2 py-1 text-xs text-zinc-300 transition hover:border-red-500/60 hover:text-red-300"
                        onClick={() => onRemove(record.id)}
                        type="button"
                      >
                        Remove
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </section>
  );
}
