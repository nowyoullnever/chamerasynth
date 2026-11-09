// Offline Phase 6 follow-up exporter. It requires an authorized local import;
// it never writes the stock firmware or produces a patch.
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
import ghidra.program.model.symbol.Reference;

public class ExportPhase6Boundaries extends GhidraScript {
    private static final long BIAS = 0x200;
    private static final long[] TARGETS = {0x25984, 0x8f67c, 0x63b0, 0x1c9c4, 0x6134, 0x2d31c, 0x12f0c, 0x133f0};
    private static String q(String value) { return "\"" + value.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n") + "\""; }
    private static String va(Address address) { return String.format("0x%08x", address.getOffset()); }
    private static String file(long value) { return String.format("0x%06x", value + BIAS); }
    private Address at(long value) { return currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(value); }
    private List<String> incoming(Address address) { List<String> rows = new ArrayList<>(); for (Reference ref : currentProgram.getReferenceManager().getReferencesTo(address)) rows.add(va(ref.getFromAddress()) + "->" + va(ref.getToAddress()) + ":" + ref.getReferenceType()); return rows; }
    private List<String> directCalls(Function function) { List<String> rows = new ArrayList<>(); InstructionIterator instructions = currentProgram.getListing().getInstructions(function.getBody(), true); while (instructions.hasNext()) { Instruction instruction = instructions.next(); if (instruction.getFlowType().isCall()) for (Address target : instruction.getFlows()) rows.add(va(instruction.getAddress()) + "->" + va(target)); } return rows; }
    private void array(PrintWriter out, List<String> rows) { out.print("["); for (int i = 0; i < rows.size(); i++) { if (i != 0) out.print(","); out.print(q(rows.get(i))); } out.print("]"); }

    @Override public void run() throws Exception {
        if (getScriptArgs().length != 1) throw new IllegalArgumentException("output directory required");
        File root = new File(getScriptArgs()[0]); root.mkdirs();
        File pseudo = new File(root, "pseudocode"); pseudo.mkdirs();
        DecompInterface decomp = new DecompInterface(); decomp.openProgram(currentProgram);
        try (PrintWriter out = new PrintWriter(new FileWriter(new File(root, "phase6_boundary_graph.json")))) {
            out.println("{\"mapping\":\"file offset = logical VA + 0x200; hypothesis only\",\"functions\":[");
            for (int index = 0; index < TARGETS.length; index++) {
                long requested = TARGETS[index]; Address address = at(requested);
                Function function = currentProgram.getFunctionManager().getFunctionContaining(address);
                if (index != 0) out.println(",");
                out.print("{\"requested_va\":" + q(va(address)) + ",\"requested_file_offset\":" + q(file(requested)) + ",\"incoming_references\":"); array(out, incoming(address));
                if (function == null) { out.print(",\"status\":\"no_function\"}"); continue; }
                DecompileResults result = decomp.decompileFunction(function, 90, monitor);
                String name = String.format("%06x.c", function.getEntryPoint().getOffset() + BIAS);
                try (PrintWriter c = new PrintWriter(new FileWriter(new File(pseudo, name)))) { c.println("/* Phase 6 retained-boundary export; inferred decompiler output. */"); c.println(result.getDecompiledFunction() == null ? "/* no pseudocode */" : result.getDecompiledFunction().getC()); }
                out.print(",\"entry_va\":" + q(va(function.getEntryPoint())) + ",\"entry_file_offset\":" + q(file(function.getEntryPoint().getOffset())) + ",\"direct_calls\":"); array(out, directCalls(function)); out.print(",\"pseudocode_file\":" + q("pseudocode/" + name) + ",\"decompile_complete\":" + (result.decompileCompleted() ? "true" : "false") + "}");
            }
            out.println("],\"limitations\":[\"Direct callers do not recover argument dataflow or indirect targets.\",\"No runtime or hardware execution is performed.\"]}");
        } finally { decomp.dispose(); }
    }
}
