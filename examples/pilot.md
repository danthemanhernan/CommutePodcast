# The Engineering Commute: Pilot

Welcome to The Engineering Commute, a short briefing built for controls, software, and data
engineers who want useful technical ideas without spending the whole drive sorting through noise.

Today, let’s clarify one architectural distinction that appears constantly in industrial data
systems: the difference between a message broker and a durable event log. MQTT brokers are very
good at efficiently moving current device state and telemetry between publishers and subscribers.
Kafka, by contrast, is organized around retained, ordered logs that consumers can replay at their
own pace. Neither design automatically replaces the other.

Imagine a production line publishing temperatures, pressures, and equipment states. MQTT can be
the lightweight nervous system near the equipment. Kafka can become the durable historical spine
used by analytics, alerting, and downstream data products. A bridge between them lets each system
do the job it was designed to do.

The practical takeaway is simple: choose technology from delivery and retention requirements, not
from popularity. Ask whether consumers must replay history, whether ordering matters, how much
temporary disconnection you expect, and what operational complexity your team can support.

That’s today’s Engineering Commute. On the next episode, we’ll look at consumer groups and explain
why horizontal scaling creates both throughput and coordination problems.

