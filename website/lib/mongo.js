import { MongoClient } from "mongodb";

const uri = process.env.MONGO_URL;
const dbName = process.env.MONGO_DB || "dental_clinic";

if (!uri) throw new Error("MONGO_URL is not set");

// Next.js hot-reloads modules in dev, which would otherwise open a new pool on
// every edit until Mongo refuses connections. Cache the promise on globalThis.
const globalForMongo = globalThis;
const clientPromise =
  globalForMongo._mongoClientPromise ??
  (globalForMongo._mongoClientPromise = new MongoClient(uri, {
    maxPoolSize: 10,
    serverSelectionTimeoutMS: 8000,
  }).connect());

export async function db() {
  return (await clientPromise).db(dbName);
}

export async function col(name) {
  return (await db()).collection(name);
}
