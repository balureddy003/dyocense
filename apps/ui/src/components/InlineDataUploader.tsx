import { FileText, Upload } from "lucide-react";
import React, { useRef, useState } from "react";
import type { DataSource } from "./DataUploader";

interface InlineDataUploaderProps {
    format?: string;
    expectedColumns?: string[];
    onUploadComplete: (dataSource: DataSource) => void;
    onCancel?: () => void;
}

export function InlineDataUploader({
    format = "csv",
    expectedColumns,
    onUploadComplete,
    onCancel
}: InlineDataUploaderProps) {
    const [uploading, setUploading] = useState(false);
    const [progress, setProgress] = useState(0);
    const [error, setError] = useState<string | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file) return;

        setError(null);
        setUploading(true);
        setProgress(0);

        try {
            // Simulate upload progress
            const progressInterval = setInterval(() => {
                setProgress(prev => {
                    if (prev >= 90) {
                        clearInterval(progressInterval);
                        return 90;
                    }
                    return prev + 10;
                });
            }, 200);

            // Read file content
            const text = await file.text();
            const lines = text.split("\n").filter(l => l.trim());
            const headers = lines[0]?.split(",").map(h => h.trim()) || [];

            clearInterval(progressInterval);
            setProgress(100);

            // Create data source object
            const dataSource: DataSource = {
                id: `ds-${Date.now()}`,
                name: file.name.replace(/\.[^/.]+$/, ""),
                type: "file",
                status: "ready",
                metadata: {
                    size: file.size,
                    rows: lines.length - 1,
                    columns: headers,
                },
            }; setTimeout(() => {
                onUploadComplete(dataSource);
                setUploading(false);
            }, 500);

        } catch (err) {
            setError("Failed to upload file. Please try again.");
            setUploading(false);
            setProgress(0);
        }
    };

    const acceptedFormats = format === "csv" ? ".csv" :
        format === "excel" ? ".xlsx,.xls" :
            format === "json" ? ".json" :
                ".csv,.xlsx,.json";

    return (
        <div className="my-3 rounded-lg border border-gray-200 bg-gray-50 p-4">
            {expectedColumns && expectedColumns.length > 0 && (
                <div className="mb-3 rounded border border-blue-200 bg-blue-50 p-2">
                    <p className="text-xs font-medium text-blue-900 mb-1">Expected columns:</p>
                    <p className="text-xs text-blue-700">
                        {expectedColumns.join(", ")}
                    </p>
                </div>
            )}

            {!uploading ? (
                <div>
                    <label
                        onClick={() => fileInputRef.current?.click()}
                        className="flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed border-gray-300 bg-white p-6 transition-colors hover:border-blue-400 hover:bg-blue-50"
                    >
                        <input
                            ref={fileInputRef}
                            type="file"
                            accept={acceptedFormats}
                            className="hidden"
                            onChange={handleFileSelect}
                        />
                        <Upload className="mb-2 h-8 w-8 text-gray-400" />
                        <span className="text-sm font-medium text-gray-700">
                            Drop {format.toUpperCase()} file or click to browse
                        </span>
                        <span className="mt-1 text-xs text-gray-500">
                            Maximum file size: 10MB
                        </span>
                    </label>

                    {onCancel && (
                        <button
                            onClick={onCancel}
                            className="mt-2 w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                        >
                            Cancel
                        </button>
                    )}
                </div>
            ) : (
                <div className="space-y-3">
                    <div className="flex items-center gap-3">
                        <FileText className="h-5 w-5 text-blue-600" />
                        <span className="text-sm font-medium text-gray-900">Uploading...</span>
                    </div>

                    <div className="overflow-hidden rounded-full bg-gray-200">
                        <div
                            className="h-2 rounded-full bg-blue-500 transition-all duration-300"
                            style={{ width: `${progress}%` }}
                        />
                    </div>

                    <p className="text-xs text-gray-600">{progress}% complete</p>
                </div>
            )}

            {error && (
                <div className="mt-3 rounded border border-red-200 bg-red-50 p-2">
                    <p className="text-xs text-red-700">{error}</p>
                </div>
            )}
        </div>
    );
}
