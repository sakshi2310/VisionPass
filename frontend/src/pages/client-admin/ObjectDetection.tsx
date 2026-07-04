import { Camera, Map, ScanSearch, SlidersHorizontal } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { useApp } from "@/context/AppContext";
import { usePageTitle } from "@/hooks/usePageTitle";

const capabilities = [
  "Detection models and classes",
  "Detection rules",
  "Live object detection monitoring",
  "Detection events and alerts",
  "Object detection reports",
  "Camera zones / ROI",
  "Confidence thresholds",
];

export function ObjectDetectionPage() {
  const navigate = useNavigate();
  const { user } = useApp();
  const basePath = user?.role === "TENANT_ADMIN" ? "/tenant-admin" : "/client-admin";

  usePageTitle("Vision Pass | Object Detection");

  return (
    <div className="grid gap-6">
      <section className="surface-strong p-7">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.24em] text-cyan-300">Object detection</p>
            <h1 className="mt-2 text-3xl font-semibold text-white">Detection workspace</h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">
              Add cameras, view browser-compatible streams, and configure persisted detection zones.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="secondary" leftIcon={<Camera className="h-4 w-4" />} onClick={() => navigate(`${basePath}/cameras`)}>
              Add Camera
            </Button>
            <Button leftIcon={<Map className="h-4 w-4" />} onClick={() => navigate(`${basePath}/object-detection/zones`)}>
              Open Zone View
            </Button>
          </div>
        </div>
      </section>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {capabilities.map((capability) => (
          <Card key={capability} className="flex items-center gap-3">
            <SlidersHorizontal className="h-5 w-5 text-cyan-500" />
            <span className="font-medium">{capability}</span>
          </Card>
        ))}
      </section>

      <EmptyState
        title="Ready for detection cameras"
        description="Add a camera and assign it to Object Detection or Both, then open Zone View to configure regions of interest."
        action={
          <div className="flex flex-wrap justify-center gap-2">
            <Button variant="secondary" leftIcon={<Camera className="h-4 w-4" />} onClick={() => navigate(`${basePath}/cameras`)}>Add Camera</Button>
            <Button leftIcon={<ScanSearch className="h-4 w-4" />} onClick={() => navigate(`${basePath}/object-detection/zones`)}>Zone View</Button>
          </div>
        }
      />
    </div>
  );
}
