"use client"

import type React from "react"

import { useState, useRef } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Upload, X, FileText, CheckCircle } from "lucide-react"
import { apiClient } from "@/lib/api-client"

interface FileUploadItem {
  id: string
  name: string
  status: "pending" | "uploading" | "completed" | "error"
  progress: number
  error?: string
  taskId?: string
}

export function FileUploader({ knowledgeBaseId }: { knowledgeBaseId: string }) {
  const [files, setFiles] = useState<FileUploadItem[]>([])
  const [isDragging, setIsDragging] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => {
    setIsDragging(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const droppedFiles = Array.from(e.dataTransfer.files)
    handleFiles(droppedFiles)
  }

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      handleFiles(Array.from(e.target.files))
    }
  }

  const handleFiles = async (selectedFiles: File[]) => {
    const newFiles: FileUploadItem[] = selectedFiles.map((file, index) => ({
      id: `${Date.now()}-${index}`,
      name: file.name,
      status: "pending",
      progress: 0,
    }))

    setFiles((prev) => [...prev, ...newFiles])

    // Upload each file
    for (const file of selectedFiles) {
      const fileItem = newFiles.find((f) => f.name === file.name)
      if (!fileItem) continue

      try {
        setFiles((prev) => prev.map((f) => (f.id === fileItem.id ? { ...f, status: "uploading", progress: 0 } : f)))

        const formData = new FormData()
        formData.append("files", file)
        formData.append("knowledge_base_id", knowledgeBaseId)

        const response = await apiClient.postFormData("/upload-file", formData)

        if (response.results && response.results[0]) {
          const taskId = response.results[0].task_id

          setFiles((prev) =>
            prev.map((f) => (f.id === fileItem.id ? { ...f, status: "completed", progress: 100, taskId } : f)),
          )

          // Poll for task status
          pollTaskStatus(fileItem.id, taskId)
        }
      } catch (error: any) {
        setFiles((prev) =>
          prev.map((f) => (f.id === fileItem.id ? { ...f, status: "error", error: error.message } : f)),
        )
      }
    }
  }

  const pollTaskStatus = async (fileId: string, taskId: string, maxAttempts = 30) => {
    let attempts = 0

    const poll = async () => {
      try {
        const response = await apiClient.get(`/task-status/${taskId}`)

        if (response.status === "SUCCESS") {
          setFiles((prev) => prev.map((f) => (f.id === fileId ? { ...f, status: "completed", progress: 100 } : f)))
        } else if (response.status === "FAILURE") {
          setFiles((prev) =>
            prev.map((f) => (f.id === fileId ? { ...f, status: "error", error: "Processing failed" } : f)),
          )
        } else if (attempts < maxAttempts) {
          attempts++
          setTimeout(poll, 2000)
        }
      } catch (error) {
        // Retry on error
        if (attempts < maxAttempts) {
          attempts++
          setTimeout(poll, 2000)
        }
      }
    }

    poll()
  }

  const removeFile = (id: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== id))
  }

  return (
    <div className="space-y-4">
      <Card
        className={`border-2 border-dashed transition-colors ${
          isDragging ? "border-primary bg-primary/5" : "border-border hover:border-primary/50"
        }`}
      >
        <CardContent className="p-12">
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className="text-center cursor-pointer"
            onClick={() => fileInputRef.current?.click()}
          >
            <Upload className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-lg font-medium mb-2">Drop files here or click to browse</p>
            <p className="text-sm text-muted-foreground">Supported formats: PDF, DOCX, TXT, JSON, and more</p>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              onChange={handleFileInput}
              className="hidden"
              accept=".pdf,.docx,.txt,.json,.md,.csv"
            />
          </div>
        </CardContent>
      </Card>

      {files.length > 0 && (
        <Card>
          <CardContent className="p-6">
            <h3 className="font-semibold mb-4">Uploading Files ({files.length})</h3>
            <div className="space-y-4">
              {files.map((file) => (
                <div key={file.id} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 flex-1 min-w-0">
                      <FileText size={18} className="flex-shrink-0 text-muted-foreground" />
                      <span className="text-sm font-medium truncate">{file.name}</span>
                      {file.status === "completed" && (
                        <CheckCircle size={18} className="flex-shrink-0 text-green-600" />
                      )}
                    </div>
                    {file.status !== "completed" && (
                      <button onClick={() => removeFile(file.id)} className="p-1 hover:bg-secondary rounded">
                        <X size={18} />
                      </button>
                    )}
                  </div>
                  <Progress value={file.progress} className="h-2" />
                  {file.error && <p className="text-xs text-destructive">{file.error}</p>}
                  <p className="text-xs text-muted-foreground capitalize">
                    {file.status === "uploading"
                      ? "Uploading..."
                      : file.status === "completed"
                        ? "Processing complete"
                        : file.status === "error"
                          ? "Failed"
                          : "Pending"}
                  </p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
