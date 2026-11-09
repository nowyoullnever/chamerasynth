// Seeds are analysis hypotheses. Creating a Ghidra function does not prove its
// original boundary or ABI; the exporter records that distinction.
import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.app.cmd.function.CreateFunctionCmd;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.SourceType;

public class SeedCharmeraFunctions extends GhidraScript {
    private static final long[][] SEEDS = {
        {0x00000000L, 0x00000200L}, {0x0000003cL, 0x0000023cL},
        {0x0002db48L, 0x0002dd48L}, {0x000063b0L, 0x000065b0L},
        {0x00006378L, 0x00006578L}, {0x00036074L, 0x00036274L},
        {0x0002cc24L, 0x0002ce24L}, {0x0001c9c4L, 0x0001cbc4L},
        {0x00021a2cL, 0x00021c2cL}, {0x00021170L, 0x00021370L},
        {0x00021618L, 0x00021818L}, {0x000215b4L, 0x000217b4L},
        {0x00001b20L, 0x00001d20L}
    };

    @Override
    public void run() throws Exception {
        for (long[] seed : SEEDS) {
            Address address = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(seed[0]);
            DisassembleCommand disassemble = new DisassembleCommand(address, null, true);
            boolean decoded = disassemble.applyTo(currentProgram, monitor);
            Function function = currentProgram.getFunctionManager().getFunctionAt(address);
            boolean created = false;
            if (function == null) {
                CreateFunctionCmd create = new CreateFunctionCmd("seed_" + Long.toHexString(seed[1]), address,
                    null, SourceType.ANALYSIS);
                created = create.applyTo(currentProgram, monitor);
            }
            println(String.format("SEED file=0x%06x va=0x%06x decoded=%s created=%s", seed[1], seed[0], decoded, created));
        }
    }
}

