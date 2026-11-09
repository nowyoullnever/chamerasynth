// Phase 4, offline-only: export containing functions and focused call-site data.
// All VAs are logical payload VAs; file offset = VA + 0x200 is only a hypothesis.
import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.util.ArrayList;
import java.util.List;

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.mem.MemoryAccessException;
import ghidra.program.model.symbol.Reference;

public class ExportPhase4AppAnalysis extends GhidraScript {
    private static final long[] TARGETS = {
        0x25668L, 0x2572cL, 0x25a38L, 0x25984L, 0x21dc8L, 0x21d20L,
        0x220ccL, 0x6378L, 0x2e3cL, 0x257b8L, 0x21618L, 0x21170L,
        0x2db34L, 0x2daa8L, 0x24d7cL, 0x8f560L, 0x8ff2cL
    };
    private static final long FILE_BIAS = 0x200;

    private static String q(String s) {
        if (s == null) return "null";
        return "\"" + s.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n").replace("\r", "\\r") + "\"";
    }
    private static String va(Address a) { return a == null ? null : String.format("0x%08x", a.getOffset()); }
    private static String fo(long va) { return String.format("0x%06x", va + FILE_BIAS); }
    private String raw(Address a, int count) throws MemoryAccessException {
        byte[] data = new byte[count]; currentProgram.getMemory().getBytes(a, data);
        StringBuilder out = new StringBuilder(); for (byte b : data) out.append(String.format("%02x", b & 0xff)); return out.toString();
    }
    private List<String> refsTo(Address a) {
        List<String> result = new ArrayList<>();
        for (Reference r : currentProgram.getReferenceManager().getReferencesTo(a)) result.add(va(r.getFromAddress()) + "->" + va(r.getToAddress()) + " [" + r.getReferenceType().getName() + "]");
        return result;
    }
    private List<String> calls(Function f) {
        List<String> result = new ArrayList<>();
        InstructionIterator it = currentProgram.getListing().getInstructions(f.getBody(), true);
        while (it.hasNext()) { Instruction i = it.next(); if (i.getFlowType().isCall()) for (Address to : i.getFlows()) result.add(va(i.getAddress()) + "->" + va(to)); }
        return result;
    }
    private void array(PrintWriter out, List<String> values) { out.print("["); for (int i = 0; i < values.size(); i++) { if (i != 0) out.print(","); out.print(q(values.get(i))); } out.print("]"); }

    @Override public void run() throws Exception {
        if (getScriptArgs().length != 1) throw new IllegalArgumentException("expected export directory");
        File root = new File(getScriptArgs()[0]); root.mkdirs();
        DecompInterface decomp = new DecompInterface(); decomp.setSimplificationStyle("decompile"); decomp.openProgram(currentProgram);
        try (PrintWriter json = new PrintWriter(new FileWriter(new File(root, "phase4_application_graph.json")))) {
            json.println("{\"mapping\":\"file offset = logical VA + 0x200; hypothesis only\",\"targets\":[");
            boolean first = true;
            for (long target : TARGETS) {
                Address a = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(target);
                Function f = currentProgram.getFunctionManager().getFunctionContaining(a);
                if (!first) json.println(","); first = false;
                json.print("{\"target_va\":" + q(va(a)) + ",\"target_file_offset\":" + q(fo(target)) + ",\"target_head_hex\":" + q(raw(a, 16)) + ",\"incoming_references\":"); array(json, refsTo(a));
                if (f == null) { json.print(",\"status\":\"no_containing_function\"}"); continue; }
                String stem = String.format("%06x", f.getEntryPoint().getOffset() + FILE_BIAS);
                DecompileResults result = decomp.decompileFunction(f, 90, monitor);
                try (PrintWriter c = new PrintWriter(new FileWriter(new File(root, stem + ".c")))) {
                    c.println("/* target VA " + va(a) + ", target file " + fo(target) + " */");
                    c.println("/* containing entry VA " + va(f.getEntryPoint()) + ", file " + fo(f.getEntryPoint().getOffset()) + " */");
                    c.println(result.getDecompiledFunction() == null ? "/* no pseudocode */" : result.getDecompiledFunction().getC());
                }
                json.print(",\"status\":\"containing_function\",\"entry_va\":" + q(va(f.getEntryPoint())) + ",\"entry_file_offset\":" + q(fo(f.getEntryPoint().getOffset())) + ",\"body_min_va\":" + q(va(f.getBody().getMinAddress())) + ",\"body_max_va\":" + q(va(f.getBody().getMaxAddress())) + ",\"entry_head_hex\":" + q(raw(f.getEntryPoint(), 32)) + ",\"containing_incoming_references\":");
                array(json, refsTo(f.getEntryPoint())); json.print(",\"direct_call_edges\":"); array(json, calls(f));
                json.print(",\"return_type\":" + q(f.getReturnType().getDisplayName()) + ",\"pseudocode_file\":" + q(stem + ".c") + ",\"decompile_status\":" + q(result.decompileCompleted() ? "complete" : "incomplete") + "}");
            }
            json.println("],\"limitations\":[\"Function containers and decompiler types are static Ghidra analysis, not runtime proof.\",\"Target heads are original bytes at logical VA under the mapping hypothesis.\"]}");
        } finally { decomp.dispose(); }
    }
}
