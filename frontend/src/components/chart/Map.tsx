import React, { useMemo } from "react";
import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import type { NodeComponentProps } from "../../registry/registry";

interface Point {
  lat: number;
  lon: number;
  label?: string;
}

interface MapProps {
  points: Point[];
  color?: string;
  sizeKey?: string;
  zoom?: number;
  height?: number;
  useContainerWidth?: boolean;
}

export const Map: React.FC<NodeComponentProps> = ({ props }) => {
  const {
    points = [],
    color = "#FF5733",
    zoom,
    height = 400,
    useContainerWidth = true,
  } = props as MapProps;

  // Calculate center and zoom from points
  const { center, autoZoom } = useMemo(() => {
    if (!points.length) {
      return { center: [0, 0] as [number, number], autoZoom: 2 };
    }

    const lats = points.map((p) => p.lat);
    const lons = points.map((p) => p.lon);

    const minLat = Math.min(...lats);
    const maxLat = Math.max(...lats);
    const minLon = Math.min(...lons);
    const maxLon = Math.max(...lons);

    const centerLat = (minLat + maxLat) / 2;
    const centerLon = (minLon + maxLon) / 2;

    // Calculate appropriate zoom based on bounds
    const latDiff = maxLat - minLat;
    const lonDiff = maxLon - minLon;
    const maxDiff = Math.max(latDiff, lonDiff);

    let calculatedZoom = 10;
    if (maxDiff > 100) calculatedZoom = 2;
    else if (maxDiff > 50) calculatedZoom = 3;
    else if (maxDiff > 20) calculatedZoom = 4;
    else if (maxDiff > 10) calculatedZoom = 5;
    else if (maxDiff > 5) calculatedZoom = 6;
    else if (maxDiff > 2) calculatedZoom = 7;
    else if (maxDiff > 1) calculatedZoom = 8;
    else if (maxDiff > 0.5) calculatedZoom = 9;
    else if (maxDiff > 0.1) calculatedZoom = 11;
    else calculatedZoom = 13;

    return {
      center: [centerLat, centerLon] as [number, number],
      autoZoom: calculatedZoom,
    };
  }, [points]);

  if (!points.length) {
    return (
      <div
        className="flex items-center justify-center bg-gray-100 border border-gray-200 rounded-lg text-gray-400"
        style={{ height, width: useContainerWidth ? "100%" : undefined }}
      >
        No location data to display
      </div>
    );
  }

  return (
    <div
      className="rounded-lg overflow-hidden border border-gray-200"
      style={{ height, width: useContainerWidth ? "100%" : undefined }}
    >
      <MapContainer
        center={center}
        zoom={zoom ?? autoZoom}
        style={{ height: "100%", width: "100%" }}
        scrollWheelZoom={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {points.map((point, idx) => (
          <CircleMarker
            key={idx}
            center={[point.lat, point.lon]}
            radius={8}
            pathOptions={{
              color: color,
              fillColor: color,
              fillOpacity: 0.6,
            }}
          >
            {point.label && <Popup>{point.label}</Popup>}
          </CircleMarker>
        ))}
      </MapContainer>
    </div>
  );
};
