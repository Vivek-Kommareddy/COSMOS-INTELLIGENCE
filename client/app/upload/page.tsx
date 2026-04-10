import { Suspense } from "react";
import UploadClient from "./UploadClient";

export default function UploadPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-[#020208] flex items-center justify-center text-gray-500 text-sm font-mono">
          Loading...
        </div>
      }
    >
      <UploadClient />
    </Suspense>
  );
}
