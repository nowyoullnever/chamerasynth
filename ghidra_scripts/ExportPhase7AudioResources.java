// Phase 7A static exporter.  It seeds only stated hypotheses and records those
// functions as Ghidra analysis output, never as runtime observations.
import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.util.ArrayList;
import java.util.List;

import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.app.cmd.function.CreateFunctionCmd;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.SourceType;

public class ExportPhase7AudioResources extends GhidraScript {
    private static final long[] SEEDS = {0x1298, 0x1310, 0x12bd0, 0x12e48, 0x12f0c, 0x13110, 0x133f0, 0x1e234, 0x1e844, 0x1e970};
    private static final long PAYLOAD_FILE_OFFSET = 0x200;

    private String json(String value) {
        if (value == null) return "null";
        return "\"" + value.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n").replace("\r", "\\r") + "\"";
    }
    private Address address(long offset) { return currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(offset); }
    private String hex(Address value) { return value == null ? null : String.format("0x%08x", value.getOffset()); }
    private String fileOffset(Address value) { return value == null ? null : String.format("0x%06x", value.getOffset() + PAYLOAD_FILE_OFFSET); }
    private Function seed(long offset) throws Exception {
        Address target = address(offset);
        new DisassembleCommand(target, null, true).applyTo(currentProgram, monitor);
        Function function = currentProgram.getFunctionManager().getFunctionAt(target);
        if (function == null) {
            new CreateFunctionCmd("phase7a_seed_" + Long.toHexString(offset), target, null, SourceType.ANALYSIS).applyTo(currentProgram, monitor);
            function = currentProgram.getFunctionManager().getFunctionAt(target);
        }
        return function;
    }
    private void stringArray(PrintWriter out, List<String> values) {
        out.print("[");
        for (int i = 0; i < values.size(); i++) { if (i > 0) out.print(","); out.print(json(values.get(i))); }
        out.print("]");
    }

    @Override
    public void run() throws Exception {
        if (getScriptArgs().length != 1) throw new IllegalArgumentException("expected export directory argument");
        File root = new File(getScriptArgs()[0]); root.mkdirs();
        File pseudocode = new File(root, "pseudocode"); pseudocode.mkdirs();
        DecompInterface decomp = new DecompInterface(); decomp.setSimplificationStyle("decompile"); decomp.openProgram(currentProgram);
        try (PrintWriter out = new PrintWriter(new FileWriter(new File(root, "phase7a_audio_functions.json")))) {
            out.println("{\"mapping\":\"file_offset = va + 0x200; hypothesis only\",\"functions\":[");
            boolean first = true;
            for (long offset : SEEDS) {
                Function function = seed(offset);
                Address target = address(offset);
                if (!first) out.println(","); first = false;
                out.print("{\"seed_va\":" + json(hex(target)) + ",\"seed_file_offset\":" + json(fileOffset(target)));
                if (function == null) { out.print(",\"status\":\"no_function_at_seed\"}"); continue; }
                List<String> incoming = new ArrayList<String>();
                for (Reference ref : currentProgram.getReferenceManager().getReferencesTo(target)) incoming.add(hex(ref.getFromAddress()) + "->" + hex(ref.getToAddress()));
                List<String> outgoing = new ArrayList<String>();
                InstructionIterator instructions = currentProgram.getListing().getInstructions(function.getBody(), true);
                while (instructions.hasNext()) {
                    Instruction instruction = instructions.next();
                    for (Reference ref : instruction.getReferencesFrom()) outgoing.add(hex(ref.getFromAddress()) + "->" + hex(ref.getToAddress()) + ":" + ref.getReferenceType());
                }
                DecompileResults result = decomp.decompileFunction(function, 60, monitor);
                String pseudoName = String.format("pseudocode/%06x.c", function.getEntryPoint().getOffset() + PAYLOAD_FILE_OFFSET);
                try (PrintWriter pseudo = new PrintWriter(new FileWriter(new File(root, pseudoName)))) {
                    pseudo.println("/* Ghidra pseudocode; static analysis hypothesis only. */");
                    pseudo.println(result.getDecompiledFunction() == null ? "/* unavailable */" : result.getDecompiledFunction().getC());
                }
                out.print(",\"status\":\"function_at_seed\",\"entry_va\":" + json(hex(function.getEntryPoint())) + ",\"entry_file_offset\":" + json(fileOffset(function.getEntryPoint())));
                out.print(",\"incoming_references\":"); stringArray(out, incoming);
                out.print(",\"outgoing_references\":"); stringArray(out, outgoing);
                out.print(",\"decompile_status\":" + json(result.decompileCompleted() ? "complete" : "incomplete") + ",\"pseudocode_file\":" + json(pseudoName) + "}");
            }
            out.println("],\"limitations\":[\"All results are offline static analysis.\",\"Seeded function boundaries and indirect calls are unresolved hypotheses.\",\"No device, SD-card, USB, or flash operation occurred.\"]}");
        } finally { decomp.dispose(); }
    }
}
