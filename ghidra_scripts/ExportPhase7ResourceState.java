// Follow static references to RAM slots used by the resource-name resolver.
// The slots are zero in the firmware file, so this script deliberately records
// writer/reader references without claiming a reconstructed runtime table.
import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.util.LinkedHashMap;
import java.util.Map;

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.Reference;

public class ExportPhase7ResourceState extends GhidraScript {
    private static final long[] TARGETS = {0x0010b208L, 0x0010b20cL, 0x00110284L, 0x00110288L, 0x00110290L};
    private String json(String text) {
        if (text == null) return "null";
        return "\"" + text.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n").replace("\r", "\\r") + "\"";
    }
    private String hex(Address address) { return address == null ? null : String.format("0x%08x", address.getOffset()); }
    @Override public void run() throws Exception {
        if (getScriptArgs().length != 1) throw new IllegalArgumentException("expected output directory");
        File root = new File(getScriptArgs()[0]); root.mkdirs();
        File pseudo = new File(root, "pseudocode"); pseudo.mkdirs();
        Map<Long, Function> owners = new LinkedHashMap<Long, Function>();
        try (PrintWriter out = new PrintWriter(new FileWriter(new File(root, "phase7a_resource_state_refs.json")))) {
            out.println("{\"targets\":[");
            boolean firstTarget = true;
            for (long targetOffset : TARGETS) {
                if (!firstTarget) out.println(","); firstTarget = false;
                Address target = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(targetOffset);
                out.print("{\"address\":" + json(hex(target)) + ",\"references\":[");
                boolean firstRef = true;
                for (Reference reference : currentProgram.getReferenceManager().getReferencesTo(target)) {
                    if (!firstRef) out.print(","); firstRef = false;
                    Function owner = currentProgram.getFunctionManager().getFunctionContaining(reference.getFromAddress());
                    if (owner != null) owners.put(owner.getEntryPoint().getOffset(), owner);
                    out.print("{\"from\":" + json(hex(reference.getFromAddress())) + ",\"type\":" + json(reference.getReferenceType().toString()) + ",\"owner_entry\":" + json(owner == null ? null : hex(owner.getEntryPoint())) + "}");
                }
                out.print("]}");
            }
            out.println("],\"limitations\":[\"References are static only.\",\"Zero-in-file RAM slots do not reveal their runtime values or resource payload allocation.\"]}");
        }
        DecompInterface decomp = new DecompInterface(); decomp.setSimplificationStyle("decompile"); decomp.openProgram(currentProgram);
        try (PrintWriter out = new PrintWriter(new FileWriter(new File(root, "phase7a_resource_state_owners.json")))) {
            out.println("{\"owners\":["); boolean first = true;
            for (Function function : owners.values()) {
                if (!first) out.println(","); first = false;
                DecompileResults result = decomp.decompileFunction(function, 60, monitor);
                String name = String.format("pseudocode/%06x.c", function.getEntryPoint().getOffset() + 0x200);
                try (PrintWriter c = new PrintWriter(new FileWriter(new File(root, name)))) { c.println(result.getDecompiledFunction() == null ? "/* unavailable */" : result.getDecompiledFunction().getC()); }
                out.print("{\"entry\":" + json(hex(function.getEntryPoint())) + ",\"pseudocode_file\":" + json(name) + ",\"complete\":" + (result.decompileCompleted() ? "true" : "false") + "}");
            }
            out.println("],\"limitations\":[\"Pseudocode is Ghidra output, not source or runtime evidence.\"]}");
        } finally { decomp.dispose(); }
    }
}
