# 🚦 Agentic AI-Driven Multi-Agent System for Intelligent Traffic Management

> An intelligent, adaptive traffic management system that combines **Agentic AI, Multi-Agent Systems, SUMO traffic simulation, real-time telemetry, adaptive signal optimization, WebSockets, MQTT, and ESP32-based hardware control**.

---

## 📌 Overview

Urban traffic congestion is a major challenge caused by increasing vehicle density, unpredictable traffic patterns, long waiting times, and inefficient fixed-time traffic signal systems.

Traditional traffic signals operate using predefined timings and are unable to dynamically respond to changing traffic conditions.

This project proposes an **Agentic AI-Driven Multi-Agent System for Intelligent Traffic Management** that continuously monitors traffic conditions, analyzes congestion patterns, generates adaptive signal timing decisions, validates those decisions, and communicates the resulting signal commands to an ESP32-based hardware prototype.

The system uses **Eclipse SUMO (Simulation of Urban MObility)** as the traffic simulation environment and **TraCI** to obtain real-time simulation telemetry.

The project is designed as a bridge between:

**Traffic Simulation → AI Decision Making → Real-Time Dashboard → IoT Communication → Physical Traffic Signal Prototype**

---

## 🎯 Objectives

- Monitor traffic conditions continuously.
- Extract real-time traffic telemetry from SUMO.
- Analyze traffic density, vehicle count, speed, queue length, and waiting time.
- Detect congested approaches.
- Dynamically optimize traffic signal timings.
- Use multiple AI agents for decentralized decision processing.
- Provide real-time visualization through a web dashboard.
- Communicate adaptive signal commands through MQTT.
- Control traffic signal LEDs using ESP32.
- Maintain a continuous dataset of simulation telemetry.
- Provide real-time system logs and AI decision tracking.

---

# 🧠 Multi-Agent AI Architecture

The system consists of four primary intelligent agents.

```text
                  ┌─────────────────────────┐
                  │     SUMO Simulation      │
                  │    Real-Time Traffic     │
                  └────────────┬────────────┘
                               │
                               ▼
                  ┌─────────────────────────┐
                  │   Traffic Monitoring    │
                  │         Agent           │
                  │                         │
                  │ • Vehicle Count         │
                  │ • Speed                 │
                  │ • Queue Length          │
                  │ • Density               │
                  │ • Waiting Time          │
                  └────────────┬────────────┘
                               │
                               ▼
                  ┌─────────────────────────┐
                  │    Traffic Analysis     │
                  │         Agent           │
                  │                         │
                  │ • Congestion Analysis   │
                  │ • Bottleneck Detection  │
                  │ • Approach Analysis     │
                  └────────────┬────────────┘
                               │
                               ▼
                  ┌─────────────────────────┐
                  │  Signal Optimization     │
                  │         Agent            │
                  │                          │
                  │ • Adaptive Green Time    │
                  │ • Traffic Prioritization │
                  │ • Signal Optimization    │
                  └────────────┬─────────────┘
                               │
                               ▼
                  ┌─────────────────────────┐
                  │     Supervisor Agent     │
                  │                          │
                  │ • Safety Validation      │
                  │ • Decision Approval      │
                  │ • Command Dispatch       │
                  └────────────┬─────────────┘
                               │
                    ┌──────────┴──────────┐
                    ▼                     ▼
             ┌─────────────┐       ┌─────────────┐
             │   Dashboard │       │ MQTT / ESP32│
             └─────────────┘       └──────┬──────┘
                                         │
                                         ▼
                                  ┌─────────────┐
                                  │ LED Signals │
                                  └─────────────┘
