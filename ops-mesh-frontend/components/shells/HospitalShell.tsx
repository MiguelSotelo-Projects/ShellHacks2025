// components/shells/HospitalShell.tsx
"use client";

import React, { useState } from "react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ClipboardList, LineChart, Settings, UsersRound } from "lucide-react";
import Link from "next/link";
import KpiCard from "@/components/ui-ext/KpiCard";

export default function HospitalShell() {
  const [tab, setTab] = useState("overview");
  return (
    <div className="mx-auto max-w-6xl px-4 py-10">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold">Hospital Dashboard</h2>
          <p className="text-neutral-500 text-sm">Staff-facing, real-time visibility, manual actions.</p>
        </div>
        <div className="flex items-center gap-2">
          <Button asChild variant="ghost">
            <Link href="/">Back</Link>
          </Button>
          <Button variant="secondary" className="gap-2">
            <Settings className="h-4 w-4" /> Settings
          </Button>
        </div>
      </div>

      <Tabs value={tab} onValueChange={setTab} className="bg-white/70 backdrop-blur rounded-xl border p-2">
        <TabsList className="grid grid-cols-3">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="queue">Queue</TabsTrigger>
          <TabsTrigger value="kpis">KPIs</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="p-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <UsersRound className="h-5 w-5" /> Overview
              </CardTitle>
              <CardDescription>At-a-glance status of beds, transport, imaging.</CardDescription>
            </CardHeader>
            <CardContent className="text-sm text-neutral-600 space-y-2">
              <p>• Occupancy: 78% • Avg handoff: 1.8s • Active scenarios: 3</p>
              <p className="text-neutral-500">(Replace with real-time cards + swimlanes)</p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="queue" className="p-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <ClipboardList className="h-5 w-5" /> Queue
              </CardTitle>
              <CardDescription>Incoming patients (walk-in + appointments).</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <div className="rounded-md border p-3 flex items-center justify-between">
                <span>Ticket C-1027 • Walk-in • Headache</span>
                <Badge variant="secondary">ETA 14m</Badge>
              </div>
              <div className="rounded-md border p-3 flex items-center justify-between">
                <span>Appt A-991 • StepDown • Check-in started</span>
                <Badge variant="secondary">Bed pending</Badge>
              </div>
              <p className="text-neutral-500">(Replace with live list from API/WebSocket)</p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="kpis" className="p-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <LineChart className="h-5 w-5" /> KPIs
              </CardTitle>
              <CardDescription>Latency, throughput, completion %.</CardDescription>
            </CardHeader>
            <CardContent className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <KpiCard label="Handoff latency" value="1.8s" trend="good" />
              <KpiCard label="End-to-end time" value="48m" trend="warn" />
              <KpiCard label="Auto-resolved" value="92%" trend="good" />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
