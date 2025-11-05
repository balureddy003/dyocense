import { useState, useRef } from "react";
import { Upload, FileText, X, Download, CheckCircle } from "lucide-react";

interface CSVUploadProps {
  onFileSelect: (file: File, preview: any[]) => void;
  title?: string;
  description?: string;
  sampleDataUrl?: string;
}

export const CSVUpload = ({
  onFileSelect,
  title = "Upload your data",
  description = "Drag and drop your CSV file here, or click to browse",
  sampleDataUrl,
}: CSVUploadProps) => {
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const parseCSV = (text: string): any[] => {
    const lines = text.split("\n").filter((line) => line.trim());
    if (lines.length === 0) return [];

    const headers = lines[0].split(",").map((h) => h.trim());
    const rows = lines.slice(1, Math.min(6, lines.length)).map((line) => {
      const values = line.split(",").map((v) => v.trim());
      const row: any = {};
      headers.forEach((header, index) => {
        row[header] = values[index] || "";
      });
      return row;
    });

    return rows;
  };

  const handleFile = async (selectedFile: File) => {
    setError(null);

    if (!selectedFile.name.endsWith(".csv")) {
      setError("Please upload a CSV file");
      return;
    }

    if (selectedFile.size > 5 * 1024 * 1024) {
      // 5MB limit
      setError("File is too large. Maximum size is 5MB");
      return;
    }

    try {
      const text = await selectedFile.text();
      const parsedData = parseCSV(text);

      if (parsedData.length === 0) {
        setError("CSV file appears to be empty");
        return;
      }

      setFile(selectedFile);
      setPreview(parsedData);
      onFileSelect(selectedFile, parsedData);
    } catch (err) {
      setError("Failed to read file. Please check the format.");
      console.error(err);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      handleFile(droppedFile);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      handleFile(selectedFile);
    }
  };

  const handleRemove = () => {
    setFile(null);
    setPreview([]);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <div className="space-y-4">
      {!file ? (
        <div
          className={`relative rounded-xl border-2 border-dashed transition-all ${
            isDragging
              ? "border-primary bg-blue-50"
              : error
              ? "border-red-300 bg-red-50"
              : "border-gray-300 bg-gray-50 hover:border-primary hover:bg-blue-50"
          } p-8 text-center cursor-pointer`}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={handleClick}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            className="hidden"
            onChange={handleFileInput}
          />

          <div className="flex flex-col items-center gap-3">
            <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
              error ? "bg-red-100" : "bg-primary/10"
            }`}>
              <Upload size={24} className={error ? "text-red-600" : "text-primary"} />
            </div>

            <div>
              <h3 className="text-sm font-semibold text-gray-900">{title}</h3>
              <p className="text-xs text-gray-600 mt-1">{description}</p>
            </div>

            {error && (
              <p className="text-xs text-red-600 bg-red-100 px-3 py-1.5 rounded-lg">
                {error}
              </p>
            )}

            {sampleDataUrl && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  window.open(sampleDataUrl, "_blank");
                }}
                className="flex items-center gap-2 text-xs text-primary font-medium hover:underline"
              >
                <Download size={14} />
                Download sample template
              </button>
            )}
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          {/* File Info */}
          <div className="flex items-center justify-between p-4 rounded-xl border border-green-200 bg-green-50">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-green-100 flex items-center justify-center">
                <CheckCircle size={20} className="text-green-600" />
              </div>
              <div>
                <h4 className="text-sm font-semibold text-green-900">{file.name}</h4>
                <p className="text-xs text-green-700">
                  {(file.size / 1024).toFixed(1)} KB • {preview.length}+ rows
                </p>
              </div>
            </div>
            <button
              onClick={handleRemove}
              className="text-green-700 hover:text-green-900 transition"
              aria-label="Remove file"
            >
              <X size={18} />
            </button>
          </div>

          {/* Preview */}
          {preview.length > 0 && (
            <div className="rounded-xl border border-gray-200 bg-white p-4">
              <h4 className="text-xs font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <FileText size={14} />
                Preview (first 5 rows)
              </h4>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-gray-200">
                      {Object.keys(preview[0]).map((header) => (
                        <th
                          key={header}
                          className="text-left py-2 px-3 font-semibold text-gray-700 bg-gray-50"
                        >
                          {header}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {preview.map((row, index) => (
                      <tr key={index} className="border-b border-gray-100 last:border-0">
                        {Object.values(row).map((value: any, cellIndex) => (
                          <td key={cellIndex} className="py-2 px-3 text-gray-600">
                            {value}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
