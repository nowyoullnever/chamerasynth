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
import ghidra.program.model.listing.FunctionIterator;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.listing.Variable;
import ghidra.program.model.symbol.Reference;

public class ExportCharmeraAnalysis extends GhidraScript {
    private static final long[] SEEDS = {0x0,0x3c,0x2db48,0x63b0,0x6378,0x36074,0x2cc24,0x1c9c4,0x21a2c,0x21170,0x21618,0x215b4,0x1b20};
    private static final long PAYLOAD_FILE_OFFSET = 0x200;

    private static String json(String value) {
        if (value == null) return "null";
        return "\"" + value.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t") + "\"";
    }
    private static String hex(Address address) { return address == null ? null : String.format("0x%08x", address.getOffset()); }
    private static long fileOffset(Address address) { return address.getOffset() + PAYLOAD_FILE_OFFSET; }
    private static String bytes(byte[] data) {
        StringBuilder out = new StringBuilder(); for (byte b : data) out.append(String.format("%02x", b & 0xff)); return out.toString();
    }
    private static List<String> names(Iterable<Function> functions) {
        List<String> values = new ArrayList<>(); for (Function f : functions) values.add(hex(f.getEntryPoint())); return values;
    }
    private static void stringArray(PrintWriter out, List<String> values) {
        out.print("["); for (int i=0; i<values.size(); i++) { if (i>0) out.print(","); out.print(json(values.get(i))); } out.print("]");
    }

    @Override
    public void run() throws Exception {
        if (getScriptArgs().length != 1) throw new IllegalArgumentException("expected export directory argument");
        File root = new File(getScriptArgs()[0]); root.mkdirs();
        File pseudocode = new File(root, "pseudocode"); pseudocode.mkdirs();
        DecompInterface decomp = new DecompInterface(); decomp.setSimplificationStyle("decompile"); decomp.openProgram(currentProgram);
        try (PrintWriter out = new PrintWriter(new FileWriter(new File(root, "function_graph.json")))) {
            out.println("{\"mapping\":\"file_offset = va + 0x200; hypothesis only\",\"functions\":[");
            boolean first = true;
            for (long seed : SEEDS) {
                Address address = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(seed);
                Function f = currentProgram.getFunctionManager().getFunctionAt(address);
                if (!first) out.println(","); first = false;
                out.print("{\"seed_va\":" + json(hex(address)) + ",\"seed_file_offset\":" + json(String.format("0x%06x", fileOffset(address))));
                if (f == null) { out.print(",\"status\":\"no_function_at_seed\"}"); continue; }
                byte[] head = new byte[Math.min(32, (int)f.getBody().getNumAddresses())];
                currentProgram.getMemory().getBytes(f.getEntryPoint(), head);
                out.print(",\"status\":\"function_at_seed\",\"entry_va\":" + json(hex(f.getEntryPoint())) + ",\"entry_file_offset\":" + json(String.format("0x%06x", fileOffset(f.getEntryPoint()))));
                out.print(",\"body_min_va\":" + json(hex(f.getBody().getMinAddress())) + ",\"body_max_va\":" + json(hex(f.getBody().getMaxAddress())) + ",\"head_hex\":" + json(bytes(head)));
                out.print(",\"callers\":"); stringArray(out, names(f.getCallingFunctions(monitor))); out.print(",\"callees\":"); stringArray(out, names(f.getCalledFunctions(monitor)));
                List<String> calls = new ArrayList<>(); InstructionIterator instructions = currentProgram.getListing().getInstructions(f.getBody(), true);
                while (instructions.hasNext()) { Instruction i = instructions.next(); if (i.getFlowType().isCall()) for (Address to : i.getFlows()) calls.add(hex(i.getAddress()) + "->" + hex(to)); }
                out.print(",\"direct_call_edges\":"); stringArray(out, calls);
                List<String> refs = new ArrayList<>(); for (Reference ref : currentProgram.getReferenceManager().getReferencesTo(f.getEntryPoint())) refs.add(hex(ref.getFromAddress()) + "->" + hex(ref.getToAddress()));
                out.print(",\"incoming_references\":"); stringArray(out, refs);
                List<String> params = new ArrayList<>(); for (Variable v : f.getParameters()) params.add(v.getName() + ":" + v.getDataType().getDisplayName());
                List<String> locals = new ArrayList<>(); for (Variable v : f.getLocalVariables()) locals.add(v.getName() + ":" + v.getDataType().getDisplayName());
                out.print(",\"return_type\":" + json(f.getReturnType().getDisplayName()) + ",\"parameters\":"); stringArray(out, params); out.print(",\"locals\":"); stringArray(out, locals);
                DecompileResults result = decomp.decompileFunction(f, 60, monitor);
                String status = result.decompileCompleted() ? "complete" : "incomplete";
                String file = String.format("%06x.c", fileOffset(f.getEntryPoint()));
                try (PrintWriter c = new PrintWriter(new FileWriter(new File(pseudocode, file)))) { c.println("/* entry VA " + hex(f.getEntryPoint()) + ", file offset " + String.format("0x%06x", fileOffset(f.getEntryPoint())) + " */"); c.println(result.getDecompiledFunction() == null ? "/* no pseudocode */" : result.getDecompiledFunction().getC()); }
                out.print(",\"decompile_status\":" + json(status) + ",\"pseudocode_file\":" + json("pseudocode/" + file) + "}");
            }
            out.println("],\"limitations\":[\"Ghidra-generated functions and decompilation are analysis hypotheses, not runtime observations.\",\"Indirect calls, BootROM behavior, SPI mapping, and MMIO semantics remain unresolved.\"]}");
        } finally { decomp.dispose(); }
    }
}

