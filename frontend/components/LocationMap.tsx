"use client";
import { useEffect } from "react";
import { MapContainer, TileLayer, CircleMarker, useMapEvents, useMap } from "react-leaflet";

type Props={latitude:number;longitude:number;onPick:(latitude:number,longitude:number)=>void};
function Picker({onPick}: {onPick:Props["onPick"]}) {
  useMapEvents({click(event){onPick(event.latlng.lat,event.latlng.lng);}});
  return null;
}
function Recenter({latitude,longitude}:{latitude:number;longitude:number}) {
  const map=useMap();
  useEffect(()=>{map.setView([latitude,longitude]);},[map,latitude,longitude]);
  return null;
}
export default function LocationMap({latitude,longitude,onPick}:Props) {
  return <div style={{height:280,borderRadius:13,overflow:"hidden",marginTop:12,border:"1px solid #d1e3da"}}>
    <MapContainer center={[latitude,longitude]} zoom={9} scrollWheelZoom={false} style={{height:"100%",width:"100%"}}>
      <TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"/>
      <Picker onPick={onPick}/><Recenter latitude={latitude} longitude={longitude}/>
      <CircleMarker center={[latitude,longitude]} radius={8} pathOptions={{color:"#0e7554",fillColor:"#b6e698",fillOpacity:1}}/>
    </MapContainer>
  </div>;
}
