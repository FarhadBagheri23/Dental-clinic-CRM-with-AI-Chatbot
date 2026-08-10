import { col } from "./mongo";

const sum = (field) => [{ $group: { _id: null, v: { $sum: `$${field}` } } }];
const firstValue = (rows) => rows[0]?.v ?? 0;

/* ------------------------------------------------------------- dashboard */

export async function getDashboard() {
  const [invoices, payments, appointments, patients, sessions, dentists] =
    await Promise.all([
      col("invoices"),
      col("payments"),
      col("appointments"),
      col("patients"),
      col("treatment_sessions"),
      col("dentists"),
    ]);

  const [
    revenue,
    covered,
    share,
    collected,
    apptStatus,
    invoiceStatus,
    patientCount,
    sessionCount,
    dentistCount,
    upcoming,
  ] = await Promise.all([
    invoices.aggregate(sum("total_amount")).toArray(),
    invoices.aggregate(sum("insurance_covered")).toArray(),
    invoices.aggregate(sum("patient_share")).toArray(),
    payments.aggregate(sum("amount")).toArray(),
    appointments
      .aggregate([{ $group: { _id: "$status", n: { $sum: 1 } } }, { $sort: { n: -1 } }])
      .toArray(),
    invoices
      .aggregate([{ $group: { _id: "$status", n: { $sum: 1 } } }, { $sort: { n: -1 } }])
      .toArray(),
    patients.countDocuments(),
    sessions.countDocuments(),
    dentists.countDocuments(),
    appointments.countDocuments({ status: "رزرو" }),
  ]);

  const totalRevenue = firstValue(revenue);
  const totalCollected = firstValue(collected);
  const totalShare = firstValue(share);

  return {
    revenue: totalRevenue,
    insuranceCovered: firstValue(covered),
    patientShare: totalShare,
    collected: totalCollected,
    outstanding: totalShare - totalCollected,
    collectionRate: totalShare ? Math.round((totalCollected / totalShare) * 100) : 0,
    counts: {
      patients: patientCount,
      sessions: sessionCount,
      dentists: dentistCount,
      upcoming,
      appointments: apptStatus.reduce((a, r) => a + r.n, 0),
    },
    appointmentStatus: apptStatus.map((r) => ({ status: r._id, n: r.n })),
    invoiceStatus: invoiceStatus.map((r) => ({ status: r._id, n: r.n })),
  };
}

/** Revenue per dentist, derived from sessions (not invoices) so the figure
 *  stays correct when a plan spans a reporting boundary. */
export async function getDentistPerformance() {
  const sessions = await col("treatment_sessions");
  return sessions
    .aggregate([
      { $lookup: { from: "treatment_plans", localField: "plan_id", foreignField: "plan_id", as: "plan" } },
      { $unwind: "$plan" },
      { $group: { _id: "$plan.dentist_id", revenue: { $sum: "$actual_cost" }, sessions: { $sum: 1 } } },
      { $lookup: { from: "dentists", localField: "_id", foreignField: "dentist_id", as: "d" } },
      { $unwind: "$d" },
      {
        $project: {
          _id: 0,
          name: { $concat: ["دکتر ", "$d.first_name", " ", "$d.last_name"] },
          specialty: "$d.specialty",
          commission_rate: "$d.commission_rate",
          revenue: 1,
          sessions: 1,
        },
      },
      { $sort: { revenue: -1 } },
    ])
    .toArray();
}

export async function getTopServices(limit = 8) {
  const sessions = await col("treatment_sessions");
  return sessions
    .aggregate([
      { $group: { _id: "$service_id", n: { $sum: 1 }, revenue: { $sum: "$actual_cost" } } },
      { $lookup: { from: "services", localField: "_id", foreignField: "service_id", as: "s" } },
      { $unwind: "$s" },
      { $project: { _id: 0, name: "$s.name", category: "$s.category", n: 1, revenue: 1 } },
      { $sort: { revenue: -1 } },
      { $limit: limit },
    ])
    .toArray();
}

export async function getLowStock() {
  const consumables = await col("consumables");
  return consumables
    .aggregate([
      { $match: { $expr: { $lte: ["$stock_quantity", { $multiply: ["$min_stock_level", 1.5] }] } } },
      { $addFields: { critical: { $lte: ["$stock_quantity", "$min_stock_level"] } } },
      { $project: { _id: 0 } },
      { $sort: { critical: -1, stock_quantity: 1 } },
    ])
    .toArray();
}

/* ----------------------------------------------------------------- lists */

const PAGE_SIZE = 20;

function pageMeta(total, page) {
  const pages = Math.max(Math.ceil(total / PAGE_SIZE), 1);
  return { total, page: Math.min(page, pages), pages, size: PAGE_SIZE };
}

export async function listPatients({ q = "", page = 1 } = {}) {
  const patients = await col("patients");
  const filter = q
    ? {
        $or: [
          { first_name: { $regex: q, $options: "i" } },
          { last_name: { $regex: q, $options: "i" } },
          { national_code: { $regex: `^${q.replace(/\D/g, "")}` } },
          { phone: { $regex: q.replace(/\D/g, "") } },
        ],
      }
    : {};

  const total = await patients.countDocuments(filter);
  const meta = pageMeta(total, page);
  const rows = await patients
    .aggregate([
      { $match: filter },
      { $sort: { patient_id: -1 } },
      { $skip: (meta.page - 1) * PAGE_SIZE },
      { $limit: PAGE_SIZE },
      { $lookup: { from: "insurance", localField: "insurance_id", foreignField: "insurance_id", as: "ins" } },
      {
        $project: {
          _id: 0,
          patient_id: 1, national_code: 1, first_name: 1, last_name: 1,
          gender: 1, phone: 1, birth_date: 1, registration_date: 1, allergies: 1,
          insurance: { $ifNull: [{ $first: "$ins.company_name" }, null] },
        },
      },
    ])
    .toArray();

  return { rows, meta };
}

export async function listAppointments({ status = "", page = 1 } = {}) {
  const appointments = await col("appointments");
  const filter = status ? { status } : {};

  const total = await appointments.countDocuments(filter);
  const meta = pageMeta(total, page);
  const rows = await appointments
    .aggregate([
      { $match: filter },
      { $sort: { scheduled_datetime: -1 } },
      { $skip: (meta.page - 1) * PAGE_SIZE },
      { $limit: PAGE_SIZE },
      { $lookup: { from: "patients", localField: "patient_id", foreignField: "patient_id", as: "p" } },
      { $lookup: { from: "dentists", localField: "dentist_id", foreignField: "dentist_id", as: "d" } },
      {
        $project: {
          _id: 0,
          appointment_id: 1, scheduled_datetime: 1, status: 1, chair_number: 1,
          patient: { $concat: [{ $first: "$p.first_name" }, " ", { $first: "$p.last_name" }] },
          dentist: { $concat: ["دکتر ", { $first: "$d.first_name" }, " ", { $first: "$d.last_name" }] },
          specialty: { $first: "$d.specialty" },
        },
      },
    ])
    .toArray();

  return { rows, meta };
}

export async function listInvoices({ status = "", page = 1 } = {}) {
  const invoices = await col("invoices");
  const filter = status ? { status } : {};

  const total = await invoices.countDocuments(filter);
  const meta = pageMeta(total, page);
  const rows = await invoices
    .aggregate([
      { $match: filter },
      { $sort: { issue_date: -1 } },
      { $skip: (meta.page - 1) * PAGE_SIZE },
      { $limit: PAGE_SIZE },
      { $lookup: { from: "patients", localField: "patient_id", foreignField: "patient_id", as: "p" } },
      { $lookup: { from: "payments", localField: "invoice_id", foreignField: "invoice_id", as: "pay" } },
      {
        $project: {
          _id: 0,
          invoice_id: 1, issue_date: 1, total_amount: 1, insurance_covered: 1,
          patient_share: 1, status: 1,
          patient: { $concat: [{ $first: "$p.first_name" }, " ", { $first: "$p.last_name" }] },
          paid: { $sum: "$pay.amount" },
        },
      },
      { $addFields: { balance: { $subtract: ["$patient_share", "$paid"] } } },
    ])
    .toArray();

  return { rows, meta };
}
